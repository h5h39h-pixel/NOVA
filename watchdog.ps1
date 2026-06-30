<#
  Keep-alive watchdog for the AI Control Center (STB-1).
  Relaunches server.py automatically if it stops responding on :8900.

  Usage:
    powershell -ExecutionPolicy Bypass -File watchdog.ps1            # leave running
    powershell -ExecutionPolicy Bypass -File watchdog.ps1 -Once      # single check (for tests)

  Hardening over the original:
   - resolves a REAL python (the bare `python` often resolves to the Windows Store stub, which
     would make every restart silently fail);
   - logs to watchdog.log with timestamps;
   - requires N consecutive failed probes before restarting (ignores transient blips);
   - re-checks liveness after a restart so it doesn't spawn duplicates.
#>
param(
  [int]$IntervalSec = 15,
  [int]$FailsBeforeRestart = 2,
  [switch]$Once
)
$ErrorActionPreference = 'SilentlyContinue'
$dir = 'C:\AI\agent-workspace\control-center'
$logFile = Join-Path $dir 'watchdog.log'
$url = 'http://localhost:8900/api/health'

function Write-Log($msg) {
  $line = ("[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg)
  Write-Host $line
  try { Add-Content -Path $logFile -Value $line -Encoding utf8 } catch {}
}

function Resolve-Python {
  # Prefer a real interpreter; never the WindowsApps execution-alias stub.
  $cands = New-Object System.Collections.Generic.List[string]
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($cmd) { $cands.Add($cmd.Source) }
  Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue |
    ForEach-Object { $cands.Add($_.FullName) }
  $cands.Add("$env:ProgramFiles\Python312\python.exe")
  $cands.Add("$env:ProgramFiles\Python311\python.exe")
  foreach ($c in $cands) {
    if ($c -and (Test-Path $c) -and ($c -notlike '*WindowsApps*')) {
      try { & $c -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { return $c } } catch {}
    }
  }
  return $null
}

function Test-ServerUp {
  try { Invoke-RestMethod $url -TimeoutSec 4 | Out-Null; return $true } catch { return $false }
}

function Start-Server($py) {
  if (-not $py) { Write-Log "ERROR: no real python found - cannot restart (is Python installed?)"; return }
  Write-Log ("Control Center not responding - restarting with {0}" -f $py)
  Start-Process -WindowStyle Hidden $py -ArgumentList 'server.py' -WorkingDirectory $dir
  Start-Sleep 8
  if (Test-ServerUp) { Write-Log "restart OK - server is responding again" }
  else { Write-Log "restart attempted - still not responding (will retry)" }
}

if ($Once) {
  $py = Resolve-Python
  $up = Test-ServerUp
  Write-Log ("self-check: python={0} server_up={1}" -f ($(if ($py) { $py } else { '<none>' })), $up)
  if (-not $py) { exit 2 }   # the failure mode that made the old watchdog useless
  exit 0
}

Write-Log "Nova watchdog started - monitoring $url"
$py = Resolve-Python
if (-not $py) { Write-Log "WARNING: no real python resolved at startup; will re-resolve on demand" }
$fails = 0
while ($true) {
  if (Test-ServerUp) {
    if ($fails -gt 0) { Write-Log "server healthy again" }
    $fails = 0
  } else {
    $fails++
    Write-Log ("probe failed ({0}/{1})" -f $fails, $FailsBeforeRestart)
    if ($fails -ge $FailsBeforeRestart) {
      if (-not $py) { $py = Resolve-Python }
      Start-Server $py
      $fails = 0
    }
  }
  Start-Sleep $IntervalSec
}
