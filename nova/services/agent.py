# -*- coding: utf-8 -*-
"""Agent Mode — an autonomous ReAct loop. The model emits one JSON step at a time
({thought, action, args} or {thought, final}); `agent_tool` executes the action and
the observation is fed back until `final` or the step budget runs out.

Dependencies are all nova.* services (db, events, audit, notifications, ollama, kb,
browser, screen) except `run_action` — the ProcMgr-backed action dispatcher — which is
injected by server.py via `set_run_action()` to avoid importing the composition root."""
import json
import time
import threading
import subprocess
from pathlib import Path
from config import WORKSPACE
from nova.core.db import db
from nova.core.events import push
from nova.core.process import ps_args
from nova.services.audit import audit
from nova.services.notifications import add_notification
from nova.services.ollama import ollama_chat_once
from nova.services.kb import kb_search
from nova.services.browser import open_url_default, visible_browse
from nova.services import screen as screen_svc

# ---- injected dependency: the ProcMgr-backed action dispatcher (speak/video/…) ----
_run_action = None
def set_run_action(fn):
    """server.py injects run_action here so the agent can drive jobs without a back-import."""
    global _run_action
    _run_action = fn

def run_action(action, params, name="agent"):
    if _run_action is None:
        return f"action '{action}' unavailable (dispatcher not wired)"
    return _run_action(action, params, name)


AGENT_HEADER = (
    "You are an autonomous agent running on the user's local Windows PC. Achieve the GOAL by "
    "reasoning step by step and using tools. Respond with ONLY ONE JSON object per step — no text outside JSON.\n"
    'To use a tool: {"thought":"brief reasoning","action":"<tool>","args":{...}}\n'
    'When the goal is complete: {"thought":"brief","final":"the answer/summary for the user"}\n'
    "Available tools:\n"
)
AGENT_TOOL_DEFS = {
    "kb_search": "- kb_search {query}: search the user's knowledge base of documents (use this for questions about their files).\n",
    "run_command": "- run_command {command}: run a PowerShell command and read its output.\n",
    "open_url": ("- open_url {url}: open a URL in the user's DEFAULT browser (Chrome/Edge) as a real, visible window. "
                 "Use this when the user says 'open <site>' (e.g. open Google, open my dashboard) or to play a known video link.\n"),
    "browse": ("- browse {url, search, click_first, fill, click}: open a REAL, VISIBLE browser window the user can watch. "
               "To search YouTube, pass search='the query'; add click_first=true to open and PLAY the first video. "
               "Otherwise pass url to navigate (optionally fill {selector:value} and click selectors). "
               "The window stays open so the user sees it. Prefer this for 'search YouTube', 'watch a video', or interacting with a site.\n"),
    "see_screen": ("- see_screen {question}: look at the user's screen with a vision model and describe what is on it "
                   "(application, visible text, buttons, menus, what the user is doing). Use this for 'what is on my screen'.\n"),
    "read_screen": "- read_screen {vision}: capture the screen and extract its text via OCR (set vision=true to use the vision model).\n",
    "screenshot": "- screenshot {}: capture the current screen to an image file and return its path.\n",
    "act_on_screen": ("- act_on_screen {instruction, text, key}: ACT on the screen — locate the UI element described by "
                      "instruction (e.g. 'the search bar', 'the OK button') with the vision model, click it, then "
                      "optionally type `text` or press `key` (e.g. 'enter'). Use to operate apps you can see.\n"),
    "generate_video": "- generate_video {prompt}: start a local video generation in the background.\n",
    "notify": "- notify {text}: send the user a desktop notification.\n",
    "speak": "- speak {text}: read text aloud to the user.\n",
    "read_file": ("- read_file {path}: read a text file's contents. For a file you created, pass just its "
                  "name (e.g. notes.txt) — it is read from your output folder. Use a full path for files elsewhere.\n"),
    "write_file": ("- write_file {path, content}: write a text file. Pass just a bare filename (e.g. report.txt) — "
                   "it is saved in your output folder automatically; do NOT prefix 'agent-output/'.\n"),
    "schedule": "- schedule {name, action, params, interval_sec}: create a background automation.\n",
}
AGENT_FOOTER_TMPL = (
    "- ask {{text}}: if the goal is ambiguous or you need information only the user has, ask them and stop.\n"
    "Rules: exactly one JSON object per step. Only use the tools listed above — never invent tools "
    "(there is no 'parse_text'; reason over observations yourself). 'final' is NOT an action — to finish, "
    "output {{\"thought\":\"...\",\"final\":\"...\"}}. Prefer kb_search before answering about the user's documents. "
    "Take one action, observe, continue. Finish within {max_steps} steps."
)
def build_agent_sys(tools=None, max_steps=8):
    names = [k for k in AGENT_TOOL_DEFS if (tools is None or k in tools)]
    if not names: names = list(AGENT_TOOL_DEFS)  # never leave the agent toolless
    return AGENT_HEADER + "".join(AGENT_TOOL_DEFS[k] for k in names) + AGENT_FOOTER_TMPL.format(max_steps=max_steps)
AGENT_SYS = build_agent_sys()
# Destructive-command denylist is centralized in nova/core/safety.py (shared with the Terminal).
from nova.core.safety import danger_reason

def parse_action(text):
    s = text.find("{");
    if s < 0: return None
    depth = 0
    for i in range(s, len(text)):
        if text[i] == "{": depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try: return json.loads(text[s:i+1])
                except Exception: return None
    return None

SAFE_WRITE_ROOT = WORKSPACE / "agent-output"
DENY_READ = (".ssh", ".aws", ".env", "credentials", "login data", "id_rsa", "id_ed25519",
             "ntuser.dat", "\\.git\\config", ".npmrc", ".pypirc")
def _strip_output_prefix(p):
    """Models naturally prefix paths with 'agent-output/' or 'output/' because the tool docs
    name that folder — which would nest a doubled directory. Strip a single leading copy so a
    relative path resolves cleanly under SAFE_WRITE_ROOT."""
    s = str(p).replace("\\", "/").lstrip("/")
    low = s.lower()
    for pre in ("agent-output/", "output/"):
        if low.startswith(pre):
            return s[len(pre):]
    return s
def safe_read_path(p):
    try: rp = Path(p)
    except Exception: return None
    return None if any(d in str(rp).lower() for d in DENY_READ) else rp
def resolve_read_path(p):
    """Where to read from: absolute paths as-is; relative paths resolve against the agent's
    output folder first (so it can read files it just wrote), matching safe_write_path."""
    if safe_read_path(p) is None:
        return None
    rp = Path(p)
    if not rp.is_absolute():
        rp = SAFE_WRITE_ROOT / _strip_output_prefix(p)
    return rp
def safe_write_path(p):
    try:
        rp = Path(p)
        if not rp.is_absolute(): rp = SAFE_WRITE_ROOT / _strip_output_prefix(p)
        rp = rp.resolve(); root = SAFE_WRITE_ROOT.resolve()
        return rp if (rp == root or root in rp.parents) else None
    except Exception: return None

def agent_tool(name, args, dry_run=False, unrestricted=False):
    a = args or {}
    try:
        # read-only tools always run (so dry-run plans are grounded in real data)
        if name == "kb_search":
            hits = kb_search(a.get("query", ""), 4)
            return "\n".join(f"[{h['doc']}] {h['text'][:400]}" for h in hits) or "no results in knowledge base"
        if name == "read_file":
            p = resolve_read_path(a.get("path", ""))
            if not p: return "BLOCKED: that path is not readable (credential store)."
            if not p.exists(): return f"file not found: {p}"
            audit("agent", "read_file", str(p))
            return p.read_text(encoding="utf-8", errors="replace")[:4000]
        if name == "notify":
            add_notification("info", "Agent", a.get("text", "")); return "user notified"
        if name == "speak":
            if dry_run: return "[dry-run] would speak the text"
            run_action("speak", {"text": a.get("text", "")}); return "spoke to the user"
        # side-effecting tools are simulated in dry-run
        if name == "run_command":
            cmd = a.get("command", "")
            from nova.services.settings import exec_allowed
            if not exec_allowed():
                audit("agent", "run_command", cmd, "blocked")
                return "BLOCKED: command execution is disabled while the server is exposed on the LAN (enable 'allow_remote_exec' in Settings)."
            _why = None if unrestricted else danger_reason(cmd)
            if _why:
                audit("agent", "run_command", cmd, "blocked")
                return f"BLOCKED: that command looks destructive ({_why}). Enable Full Access to run it."
            if dry_run: return f"[dry-run] would run command: {cmd}"
            audit("agent", "run_command", cmd, "ok" if not unrestricted else "full-access")
            out = subprocess.run(ps_args(cmd), capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
            return (out.stdout or out.stderr or "(no output)")[:1500]
        if name == "write_file":
            if dry_run: return f"[dry-run] would write {len(a.get('content',''))} chars to {a.get('path','')}"
            if unrestricted:
                rp = Path(a.get("path", ""))
                if not rp.is_absolute(): rp = SAFE_WRITE_ROOT / _strip_output_prefix(a.get("path", ""))
            else:
                rp = safe_write_path(a.get("path", ""))
                if not rp: return f"BLOCKED: writes are confined to {SAFE_WRITE_ROOT}. Enable Full Access to write elsewhere."
            rp.parent.mkdir(parents=True, exist_ok=True); rp.write_text(a.get("content", ""), encoding="utf-8")
            audit("agent", "write_file", str(rp), "ok" if not unrestricted else "full-access")
            return f"wrote {len(a.get('content',''))} chars to {rp}"
        if name == "open_url":
            url = a.get("url", "")
            if dry_run: return f"[dry-run] would open {url} in the default browser"
            u = open_url_default(url); audit("agent", "open_url", u)
            return f"opened {u} in your default browser (a real window the user can see)."
        if name == "browse":
            url = a.get("url", ""); search = a.get("search"); click_first = bool(a.get("click_first"))
            if dry_run: return f"[dry-run] would open a visible browser for {search or url}"
            try:
                r = visible_browse(url=url or None, search=search, click_first=click_first,
                                   fill=a.get("fill"), click=a.get("click"))
                audit("agent", "browse", search or url, "full-access" if unrestricted else "ok")
            except Exception as e:
                if url:  # fall back to the default browser so the user still sees something
                    u = open_url_default(url); audit("agent", "browse", f"{url} (fallback)", "fallback")
                    return f"opened {u} in your default browser (visible-browser fallback: {e})."
                return f"browse error: {e}"
            if search:
                lines = [f"Opened a real browser and searched YouTube for '{r.get('query')}'. Top results:"]
                for i, v in enumerate(r.get("results", [])[:5], 1): lines.append(f"  {i}. {v['title']}")
                if r.get("opened"): lines.append(f"Now playing in the browser: {r['opened']['title']} ({r['opened']['url']})")
                elif r.get("click_error"): lines.append(f"(could not auto-click first video: {r['click_error']})")
                return "\n".join(lines)
            return f"Opened a real, visible browser window at {r.get('url')} — title: {r.get('title')}"
        if name == "see_screen":
            if dry_run: return "[dry-run] would look at the screen with the vision model"
            r = screen_svc.describe_screen(a.get("question"))
            audit("agent", "see_screen", (r.get("description") or "")[:60])
            return r.get("description") or ("error: " + r.get("error", "could not read screen"))
        if name == "read_screen":
            if dry_run: return "[dry-run] would OCR the screen"
            r = screen_svc.read_screen(bool(a.get("vision")))
            audit("agent", "read_screen", f"{len(r.get('text',''))} chars")
            return "screen text:\n" + ((r.get("text") or "(no text found)")[:1500])
        if name == "screenshot":
            if dry_run: return "[dry-run] would capture the screen"
            fn, _ = screen_svc.capture_screenshot(); audit("agent", "screenshot", fn)
            return f"captured the screen: /files/{fn}"
        if name == "act_on_screen":
            instr = a.get("instruction", "")
            if dry_run: return f"[dry-run] would locate '{instr}', click it" + (f" and type '{a.get('text')}'" if a.get("text") else "")
            r = screen_svc.act_on_screen(instr, a.get("text"), a.get("key"), bool(a.get("double")))
            audit("agent", "act_on_screen", f"{instr[:40]} -> {r.get('clicked')}", "ok" if r.get("ok") else "fail")
            if r.get("ok"):
                return f"clicked at {r.get('clicked')}" + (f", typed '{r.get('typed')}'" if r.get("typed") else "") + (f", pressed {r.get('key')}" if r.get("key") else "")
            return f"could not act: {r.get('error', 'element not found')}"
        if name == "generate_video":
            if dry_run: return "[dry-run] would start a video generation"
            run_action("video", {"prompt": a.get("prompt", "a cinematic shot")}); return "video generation started in the background"
        if name == "schedule":
            if dry_run: return f"[dry-run] would schedule '{a.get('name','task')}' ({a.get('action')})"
            c = db(); c.execute("INSERT INTO schedules(name,action,params,interval_sec,next_run,enabled,created) VALUES(?,?,?,?,?,1,?)",
                (a.get("name", "Agent task")[:80], a.get("action", "notify"), json.dumps(a.get("params", {})),
                 int(a.get("interval_sec", 0)), time.time() + 60, time.time())); c.commit(); c.close()
            return "automation scheduled"
    except Exception as e:
        return f"tool error: {e}"
    return f"unknown tool '{name}'"

AGENT_STOP = threading.Event()

def agent_run(goal, model, dry_run=False, unrestricted=False, temperature=0.2, max_steps=8, tools=None):
    AGENT_STOP.clear()
    try: max_steps = max(1, min(int(max_steps or 8), 25))
    except Exception: max_steps = 8
    try: temperature = max(0.0, min(float(temperature), 1.5))
    except Exception: temperature = 0.2
    allowed = set(tools) if tools else None
    push({"type": "agent", "ev": "start", "goal": goal, "model": model, "dry_run": dry_run,
          "unrestricted": unrestricted, "max_steps": max_steps})
    audit("agent", "goal", ("[dry-run] " if dry_run else "") + ("[full-access] " if unrestricted else "") + goal)
    sys_prompt = build_agent_sys(allowed, max_steps)
    if unrestricted:
        sys_prompt += ("\nFULL-ACCESS mode: the user has granted you full permission to control this PC — "
                       "run any PowerShell command and write files anywhere. Be capable and decisive: attempt what is asked. "
                       "Only avoid actions the user did not request.")
    if dry_run:
        sys_prompt += "\nNOTE: DRY-RUN mode — describe what you would do; side-effecting tools are simulated."
    msgs = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": "GOAL: " + goal}]
    final = None
    for step in range(max_steps):
        if AGENT_STOP.is_set():
            push({"type": "agent", "ev": "stopped"}); final = "Stopped by user."; break
        try: text = ollama_chat_once(model, msgs, temperature)
        except Exception as e:
            push({"type": "agent", "ev": "error", "text": str(e)}); break
        obj = parse_action(text)
        if not obj:
            msgs.append({"role": "assistant", "content": text})
            msgs.append({"role": "user", "content": "Respond with ONLY one JSON object exactly as instructed."})
            push({"type": "agent", "ev": "thought", "step": step + 1, "text": "(reformatting…)"})
            continue
        push({"type": "agent", "ev": "thought", "step": step + 1, "text": obj.get("thought", "")})
        if "final" in obj:
            final = obj["final"]; push({"type": "agent", "ev": "final", "text": final}); break
        action = obj.get("action", "?"); aargs = obj.get("args", {})
        if action == "ask":
            push({"type": "agent", "ev": "ask", "text": aargs.get("text", "Could you clarify the goal?")})
            add_notification("info", "Agent needs clarification", aargs.get("text", "")[:60]); final = "asked"; break
        if AGENT_STOP.is_set():
            push({"type": "agent", "ev": "stopped"}); final = "Stopped by user."; break
        if allowed is not None and action in AGENT_TOOL_DEFS and action not in allowed:
            obs = f"the '{action}' tool is disabled for this run. Choose a different approach or finish."
        else:
            push({"type": "agent", "ev": "action", "action": action, "args": aargs})
            obs = agent_tool(action, aargs, dry_run, unrestricted)
            push({"type": "agent", "ev": "observation", "text": obs[:1500]})
        msgs.append({"role": "assistant", "content": text})
        msgs.append({"role": "user", "content": "Observation: " + obs[:1500] + "\nContinue with the next JSON step."})
    if final is None:
        push({"type": "agent", "ev": "final", "text": "Reached the step limit. Partial progress shown above."})
    add_notification("success", "Agent finished", goal[:60])
    push({"type": "agent", "ev": "done"})
