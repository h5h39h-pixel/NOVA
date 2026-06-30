# Command-execution audit (SEC-6)

Review of every place the app runs an external process. **Date: 2026-06-30.**

## Method
Enumerated all `subprocess.run/Popen`, `os.startfile`, `os.system`, and `PM.start` call sites.
Checked for: `shell=True` (none), string-built shell commands, and **unsanitized user input**.

## Result
- **No `shell=True` anywhere.** Every call uses **argv-list form**, so shell-metacharacter
  injection is not possible via the argument vector.
- The arbitrary-PowerShell capability (`ps_args` → `powershell -EncodedCommand <base64>`) is the
  **intended exec feature** (Terminal + agent), gated by: localhost-default bind, `exec_allowed()`
  LAN gate, and the SEC-1/SEC-2 destructive-command confirm/denylist.

## Call sites
| Site | Form | Input | Verdict |
|---|---|---|---|
| `services/jobs.py` `PM.start`→`Popen(job.args)` | argv list | commands built via `ps_args` (base64) | OK — intended exec; gated |
| `services/agent.py` run_command `subprocess.run(ps_args(cmd))` | argv | agent/user cmd | OK — intended; gated + denylist |
| `services/schedules.py` / `tts.py` `ps_args(f'& speak.ps1 {_q(text)}')` | argv | `text` quoted via `_q` | OK — quoted + base64-wrapped |
| `services/files.py` OCR `["powershell","-File","ocr.ps1",path]` | argv | server-created temp `path` | OK — single argv element |
| `services/screen.py` OCR `["powershell","-Command",full]` | argv with built string | **`lang` from request** | **FIXED** — was interpolated unquoted → now allowlisted (`_valid_lang`) |
| `services/metrics.py` nvidia-smi / WMI temp | argv, fixed | none | OK |
| `services/owui.py` `["docker","exec",CTR,"python","-c",code]` | argv | `code` = our constants; `tool_id`/`target` via `repr()` | OK — repr-escaped, our own scripts |
| `services/browser.py` `os.startfile(url)` / `["cmd","/c","start","",url]` | argv | normalized url | OK — argv element; local |
| `services/training.py` harvest/taskkill | argv, fixed | pids (int) | OK |
| `core/process.py` `ps_args` | builds base64 `-EncodedCommand` | the command itself | OK — by design |

## Fix applied (this pass)
- **`screen.py` `read_screen(lang=…)`**: the OCR language was concatenated into a PowerShell
  `-Command` string unquoted. Since `/api/screen/read` is **not** behind the exec gate, a crafted
  `lang` could inject shell content (a real bypass if exposed on LAN). Now restricted to an
  allowlist `^[A-Za-z]{2,8}(\+[A-Za-z]{2,8})*$` via `_valid_lang()`; anything else is ignored.

## Residual / notes
- `_q()` returns a bare token unquoted if it starts with `-` and has no space (intended for flags).
  For TTS text this is a harmless edge (no arbitrary exec). Tracked, not a vulnerability.
- The exec surface remains powerful by design; defense is **localhost-only + LAN gate + confirm/
  denylist**, documented in `SECURITY.md`.
