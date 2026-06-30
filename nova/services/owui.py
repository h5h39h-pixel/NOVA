# -*- coding: utf-8 -*-
"""Open WebUI integration — runs python inside the open-webui Docker container to
read/patch its webui.db (tools, models, config). Depends only on subprocess + the
OWUI_CTR container name from config."""
import subprocess
from config import OWUI_CTR

# System prompt forced onto OWUI tool-models so they always call tools (never emit code).
FORCED_SYS = (
    "You are a command-execution assistant with tools. For ANY request to run a command, read a file, "
    "write a file, list files, or delete a file, you MUST call the matching tool: "
    "run_command(command), read_file(path), write_file(path, content), list_files(), delete_file(path). "
    "NEVER write or display Python or shell code. NEVER explain how to do it manually. "
    "Call the tool and present only its output. Default location is /host_desktop. "
    "Pass filenames exactly as given, including Arabic names."
)


def owui_py(code):
    """Run python inside the open-webui container against webui.db; return stdout text."""
    try:
        out = subprocess.run(["docker", "exec", OWUI_CTR, "python", "-c", code],
                             capture_output=True, text=True, timeout=30)
        return (out.stdout or "") + (("\n" + out.stderr) if out.returncode else "")
    except Exception as e:
        return f"__ERR__ {e}"


# NOTE: the `tool` and `model` tables are stable across OWUI versions. The `config` table
# changed in OWUI 0.10.x: the old single-row JSON blob (id, data) was reshaped into per-key
# rows (key, value). These scripts detect the live schema and read/write either form, so the
# integration keeps working before AND after an OWUI upgrade.
OWUI_LIST = r"""
import sqlite3, json
c=sqlite3.connect('/app/backend/data/webui.db'); c.row_factory=sqlite3.Row
tools=[{'id':r['id'],'name':r['name']} for r in c.execute("select id,name from tool")]
models=[]
for r in c.execute("select id,name,base_model_id,params,meta from model"):
    p=json.loads(r['params']) if r['params'] else {}
    m=json.loads(r['meta']) if r['meta'] else {}
    models.append({'id':r['id'],'name':r['name'],'base':r['base_model_id'],
        'fc':p.get('function_calling'),'temp':p.get('temperature'),
        'has_sys':bool(p.get('system')),'tools':m.get('toolIds') or []})
cols=[x[1] for x in c.execute("PRAGMA table_info(config)")]
ci=ce=None
if 'data' in cols:                       # legacy single-row blob
    row=c.execute("select data from config order by id desc limit 1").fetchone()
    cfg=json.loads(row['data']) if row and row['data'] else {}
    ci=(cfg.get('code_interpreter') or {}).get('enable')
    ce=(cfg.get('code_execution') or {}).get('enable')
else:                                    # OWUI 0.10.x per-key rows
    def _gv(k):
        r=c.execute("select value from config where key=?",(k,)).fetchone()
        if not r: return None
        try: return json.loads(r['value'])
        except Exception: return r['value']
    ci=_gv('code_interpreter.enable'); ce=_gv('code_execution.enable')
print(json.dumps({'tools':tools,'models':models,'code_interpreter':ci,'code_execution':ce}))
"""


def owui_toggle_code(tool_id, on, target="smart-tools"):
    op = f"t.add({tool_id!r})" if on else f"t.discard({tool_id!r})"
    return (
        "import sqlite3, json\n"
        "c=sqlite3.connect('/app/backend/data/webui.db'); c.row_factory=sqlite3.Row\n"
        f"r=c.execute('select meta from model where id=?', ({target!r},)).fetchone()\n"
        "m=json.loads(r['meta']) if r and r['meta'] else {}\n"
        "t=set(m.get('toolIds') or [])\n"
        f"{op}\n"
        "m['toolIds']=sorted(t)\n"
        f"c.execute(\"update model set meta=?, updated_at=strftime('%s','now') where id=?\", (json.dumps(m), {target!r})); c.commit()\n"
        "print('ok', sorted(t))\n"
    )


OWUI_APPLY = r"""
import sqlite3, json, time
SYS=%r
c=sqlite3.connect('/app/backend/data/webui.db'); c.row_factory=sqlite3.Row
done=[]
for mid in ('smart-tools','tools-assistant','hasher'):
    row=c.execute("select params from model where id=?",(mid,)).fetchone()
    if not row: continue
    p=json.loads(row['params']) if row['params'] else {}
    p['function_calling']='native'; p['temperature']=0; p['system']=SYS
    c.execute("update model set params=?, updated_at=strftime('%%s','now') where id=?",(json.dumps(p),mid))
    done.append(mid)
cols=[x[1] for x in c.execute("PRAGMA table_info(config)")]
if 'data' in cols:                       # legacy single-row blob
    row=c.execute("select id,data from config order by id desc limit 1").fetchone()
    if row:
        cfg=json.loads(row['data']) if row['data'] else {}
        for k in ('code_interpreter','code_execution'):
            d=cfg.get(k) or {}; d['enable']=False; cfg[k]=d
        c.execute("update config set data=? where id=?",(json.dumps(cfg),row['id']))
else:                                    # OWUI 0.10.x per-key rows
    for k in ('code_interpreter.enable','code_execution.enable'):
        c.execute("insert into config(key,value,updated_at) values(?,?,?) "
                  "on conflict(key) do update set value=excluded.value, updated_at=excluded.updated_at",
                  (k, json.dumps(False), int(time.time())))
c.commit()
print(json.dumps({'applied':done,'code_interpreter':False}))
""" % FORCED_SYS
