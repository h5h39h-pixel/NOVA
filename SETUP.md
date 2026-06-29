# Setup & Transfer Guide

The AI Control Center is **portable**: all paths are resolved relative to this folder
and are overridable in `config.json`. To move it to another PC, copy the folder and run
one setup command.

## First-time setup (any Windows PC)

1. Install the prerequisites (once):
   - **Python 3.10+** — https://python.org
   - **Ollama** — https://ollama.com  (provides local LLMs; `ollama pull qwen2.5:14b`)
   - *(optional)* **ComfyUI** for image/video generation, **Docker + Open WebUI** if you use it.
2. From this folder, run:
   ```powershell
   powershell -ExecutionPolicy Bypass -File setup.ps1
   ```
   This installs all Python dependencies, the headless browser (Playwright), creates
   `config.json`, and checks that Ollama/ComfyUI are reachable.
3. Start it:
   ```
   start.cmd
   ```
   Opens **http://localhost:8900**.

## Transferring to another PC

1. Copy the **`control-center`** folder (and, if you use them, the sibling `toolkit/`,
   `data/`, and the `training/` + `ComfyUI/` folders).
2. On the new PC, run `setup.ps1`, then `start.cmd`.
3. If your folders live in a different place, edit **`config.json`** — every path/URL is there:
   ```json
   {
     "workspace": "D:\\AI\\agent-workspace",
     "ai_root":   "D:\\AI",
     "ollama_url":"http://127.0.0.1:11434",
     "comfy_url": "http://127.0.0.1:8188",
     "comfy_dir": "D:\\AI\\ComfyUI",
     "training_dir":"D:\\AI\\training",
     "port": 8900,
     "https_enabled": false,
     "bind_host": ""
   }
   ```
   Defaults are derived automatically from the folder location, so if you keep the same
   layout you usually don't need to change anything.

## HTTPS (optional)

Set `"https_enabled": true` in `config.json` and restart. A self-signed certificate is
generated automatically into `data/certs/` and the dashboard is served over
**https://localhost:8900**. HTTPS is required for the **microphone** to work over a LAN
(browsers only allow mic capture on `localhost` or `https`).

## Security (optional, for LAN access)

In **Settings → Security**, enable token auth. A token is shown **once** — save it.
Only then is LAN access (`bind_host`/`lan_access`) meaningful. Tokens are stored hashed;
API access is rate-limited.

## Tests

```powershell
python run_tests.py        # 40-check live suite
```

## What runs where
- **Dashboard/API:** this folder (`server.py`, port 8900).
- **Config:** `config.json` (paths/URLs), `data/control.db` (your data — back it up!).
- **Logs:** `data/logs/server.log`.
- **Local models:** Ollama (11434). **Generation:** ComfyUI (8188). **STT:** faster-whisper (local).
