# -*- coding: utf-8 -*-
"""Backup-restore DRILL — proves a backup actually round-trips (seed → back up → wipe → restore →
verify). Runs in the gate/CI so 'we have backups' is a tested claim, not a hope."""


def test_backup_restore_roundtrip(tmpdb):
    from nova.core.db import db
    from nova.services.backup import make_backup, restore_backup

    # seed data across the backed-up tables
    c = db()
    c.execute("INSERT INTO conversations(cid,project,title,created,updated) VALUES(?,?,?,?,?)",
              ("cid-drill", "Proj", "Drill chat", 1.0, 2.0))
    c.execute("INSERT INTO chat(ts,cid,role,content) VALUES(?,?,?,?)", (1.5, "cid-drill", "user", "hello backup"))
    c.execute("INSERT INTO schedules(name,action,params,interval_sec,next_run,enabled,created) "
              "VALUES(?,?,?,?,?,?,?)", ("drill-sched", "notify", "{}", 0, None, 1, 1.0))
    c.execute("INSERT INTO workflows(name,steps,created) VALUES(?,?,?)", ("drill-wf", "[]", 1.0))
    c.commit(); c.close()

    bundle = make_backup()
    assert any(cv["cid"] == "cid-drill" for cv in bundle["conversations"])

    # simulate data loss
    c = db()
    for t in ("conversations", "chat", "schedules", "workflows"):
        c.execute(f"DELETE FROM {t}")
    c.commit()
    assert c.execute("SELECT COUNT(*) FROM conversations").fetchone()[0] == 0
    c.close()

    # restore and verify every table came back
    added = restore_backup(bundle)
    assert added is not None
    c = db()
    conv = c.execute("SELECT title FROM conversations WHERE cid='cid-drill'").fetchone()
    msg = c.execute("SELECT content FROM chat WHERE cid='cid-drill'").fetchone()
    sched = c.execute("SELECT COUNT(*) FROM schedules WHERE name='drill-sched'").fetchone()[0]
    wf = c.execute("SELECT COUNT(*) FROM workflows WHERE name='drill-wf'").fetchone()[0]
    c.close()
    assert conv and conv["title"] == "Drill chat"
    assert msg and msg["content"] == "hello backup"
    assert sched == 1 and wf == 1


def test_restore_rejects_bad_bundle(tmpdb):
    from nova.services.backup import restore_backup
    assert restore_backup({"version": 99}) is None      # unknown version → refused, no partial write
    assert restore_backup({}) is None
