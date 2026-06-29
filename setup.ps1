<#
  AI Control Center — one-command setup.
  Installs Python dependencies, the headless browser for automation, and checks
  that the local AI services are reachable. Run once on a new machine:

      powershell -ExecutionPolicy Bypass -File setup.ps1

  Then start the dashboard with:  start.cmd
#>
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $dir
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "`n=== AI Control Center setup ===" -ForegroundColor Cyan

# 1. Python
$py = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $py) { Write-Host "Python not found. Install Python 3.10+ from https://python.org and re-run." -ForegroundColor Red; exit 1 }
Write-Host ("Python: " + (python --version))

# 2. Dependencies
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip | Out-Null
python -m pip install -r requirements.txt
if (-not $?) { Write-Host "Dependency install failed." -ForegroundColor Red; exit 1 }

# 3. Headless browser (for web automation)
Write-Host "`nInstalling headless Chromium (Playwright)..." -ForegroundColor Cyan
python -m playwright install chromium

# 4. Write default config (server also auto-creates it on first run)
if (-not (Test-Path "config.json")) { python -c "import config; print('config.json created')" }

# 5. Health checks for the local AI stack (optional but recommended)
Write-Host "`n=== Local service check ===" -ForegroundColor Cyan
function Probe($name,$url){ try { Invoke-WebRequest $url -TimeoutSec 4 -UseBasicParsing | Out-Null; Write-Host ("  [OK]   {0}  ({1})" -f $name,$url) -ForegroundColor Green } catch { Write-Host ("  [MISS] {0}  ({1}) - start it or edit config.json" -f $name,$url) -ForegroundColor Yellow } }
$cfg = Get-Content config.json | ConvertFrom-Json
Probe "Ollama"   ("{0}/api/tags" -f $cfg.ollama_url)
Probe "ComfyUI"  ("{0}/system_stats" -f $cfg.comfy_url)
Probe "Open WebUI" $cfg.owui_url

Write-Host "`nSetup complete. Start the dashboard with:  start.cmd" -ForegroundColor Green
Write-Host "Then open  http://localhost:$($cfg.port)`n"
