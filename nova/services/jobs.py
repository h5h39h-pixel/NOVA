# -*- coding: utf-8 -*-
"""
Process manager — runs tracked background jobs (terminal, training, video, image…),
streams their output to dashboards, supports stop/pause/resume, and assigns each to
the Job Object so they can't orphan.

Sits in the service layer: depends on core (events, db, process) + the notifications
service. The training-completion callback is injected (set_training_hook) so this
module never has to import server.py — keeping the dependency graph acyclic.
"""
import time, threading, subprocess, re
import psutil
from nova.core.events import push
from nova.core.db import add_history, db
from nova.core.process import assign_to_job
from nova.services.notifications import add_notification


# ---- STB-2: persist jobs so a server restart doesn't silently lose them ----
def _job_insert(job, source):
    try:
        c = db()
        rid = c.execute("INSERT INTO jobs(jid,name,kind,status,started,source) VALUES(?,?,?,?,?,?)",
                        (job.id, job.name, job.kind, job.status, job.started, source)).lastrowid
        c.commit(); c.close()
        job.db_id = rid
    except Exception:
        pass


def _job_finish(job):
    try:
        if getattr(job, "db_id", None) is None: return
        c = db()
        c.execute("UPDATE jobs SET status=?, ended=?, exit_code=? WHERE id=?",
                  (job.status, time.time(), job.exit_code, job.db_id))
        c.commit(); c.close()
    except Exception:
        pass


def job_history(limit=50):
    """Recent persisted jobs (survives restarts) — includes 'interrupted' ones from prior runs."""
    try:
        c = db()
        rows = [dict(r) for r in c.execute(
            "SELECT jid,name,kind,status,started,ended,exit_code,source FROM jobs ORDER BY id DESC LIMIT ?",
            (int(limit),)).fetchall()]
        c.close()
        return rows
    except Exception:
        return []


def reconcile_interrupted():
    """On startup, any job row still 'running'/'starting'/'paused' was killed by the previous
    shutdown (the Job Object terminates children). Mark them 'interrupted' and report them so the
    user knows — training/recording can't truly resume a killed OS process, but it won't vanish."""
    try:
        c = db()
        rows = [dict(r) for r in c.execute(
            "SELECT id,name,kind FROM jobs WHERE status IN ('starting','running','paused')").fetchall()]
        if rows:
            c.execute("UPDATE jobs SET status='interrupted', ended=? WHERE status IN ('starting','running','paused')",
                      (time.time(),))
            c.commit()
        c.close()
        for r in rows:
            add_notification("error", f"{r['name']} interrupted",
                             f"a {r['kind']} job was running when the server last stopped; it did not resume",
                             category="system")
        return rows
    except Exception:
        return []

_training_hook = None
def set_training_hook(fn):
    """Server registers record_training_run here (breaks the jobs↔server cycle)."""
    global _training_hook
    _training_hook = fn

class Job:
    def __init__(self, jid, name, args, cwd=None, kind="job"):
        self.id, self.name, self.args, self.cwd, self.kind = jid, name, args, cwd, kind
        self.proc = None; self.status = "starting"; self.started = time.time()
        self.exit_code = None; self.tail = []; self.paused = False; self.db_id = None

    def info(self):
        return {"id": self.id, "name": self.name, "kind": self.kind, "status": self.status,
                "started": self.started, "exit_code": self.exit_code, "paused": self.paused,
                "pid": self.proc.pid if self.proc else None}

class ProcMgr:
    def __init__(self):
        self.jobs = {}; self._n = 0; self._lock = threading.Lock()

    def start(self, name, args, cwd=None, kind="job", source="job"):
        with self._lock:
            self._n += 1; jid = f"job{self._n}"
        job = Job(jid, name, args, cwd, kind)
        self.jobs[jid] = job
        _job_insert(job, source)
        threading.Thread(target=self._run, args=(job, source), daemon=True).start()
        return job

    @staticmethod
    def _clean(s):
        """Convert PowerShell CLIXML error noise (from parse errors) into readable text."""
        if s.strip() == "#< CLIXML": return None
        if "<Objs" in s or "<S " in s or "</S>" in s:
            s = re.sub(r"<[^>]+>", "", s).replace("_x000D__x000A_", "").replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<").rstrip()
            return s or None
        return s

    def _run(self, job, source):
        t0 = time.time()
        try:
            job.proc = subprocess.Popen(job.args, cwd=job.cwd, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True, bufsize=1,
                                        encoding="utf-8", errors="replace")
            assign_to_job(job.proc.pid)   # own the process tree (no orphans)
            job.status = "running"
            push({"type": "job", "job": job.info()})
            push({"type": "term", "job": job.id, "name": job.name, "line": f"$ {job.name}"})
            for line in job.proc.stdout:
                line = self._clean(line.rstrip("\n"))
                if line is None: continue
                job.tail.append(line); job.tail = job.tail[-500:]
                push({"type": "term", "job": job.id, "name": job.name, "line": line})
            job.proc.wait()
            job.exit_code = job.proc.returncode
            if job.status != "stopped":   # don't clobber a user-requested stop
                job.status = "done" if job.exit_code == 0 else "error"
        except Exception as e:
            job.status = "error"; job.exit_code = -1
            job.tail.append(f"[launcher error] {e}")
            push({"type": "term", "job": job.id, "name": job.name, "line": f"[error] {e}"})
        dur = time.time() - t0
        _job_finish(job)
        add_history(job.name, job.exit_code, dur, "\n".join(job.tail), source)
        push({"type": "job", "job": job.info()})
        lvl = "success" if job.exit_code == 0 else "error"
        add_notification(lvl, f"{job.name} {'finished' if lvl=='success' else 'failed'}",
                         f"exit {job.exit_code} in {dur:.0f}s")
        if job.kind == "training" and _training_hook:
            try: _training_hook(job, t0, dur)
            except Exception: pass

    def stop(self, jid):
        job = self.jobs.get(jid)
        if not job or not job.proc: return False
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(job.proc.pid)], capture_output=True)
        except Exception:
            try: job.proc.kill()
            except Exception: pass
        job.status = "stopped"
        push({"type": "job", "job": job.info()})
        return True

    def restart(self, jid):
        job = self.jobs.get(jid)
        if not job: return None
        self.stop(jid)
        return self.start(job.name, job.args, job.cwd, job.kind)

    def _tree(self, job):
        """The job process + all descendants (training spawns powershell→python grandchildren)."""
        procs = []
        try:
            p = psutil.Process(job.proc.pid)
            procs = [p] + p.children(recursive=True)
        except Exception:
            pass
        return procs

    def pause(self, jid):
        job = self.jobs.get(jid)
        if not job or not job.proc: return False
        n = 0
        for p in self._tree(job):
            try: p.suspend(); n += 1
            except Exception: pass
        if n:
            job.paused = True; job.status = "paused"
            push({"type": "job", "job": job.info()})
        return job.paused

    def resume(self, jid):
        job = self.jobs.get(jid)
        if not job or not job.proc: return False
        for p in self._tree(job):
            try: p.resume()
            except Exception: pass
        job.paused = False; job.status = "running"
        push({"type": "job", "job": job.info()})
        return True

PM = ProcMgr()
