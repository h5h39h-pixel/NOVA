<#
  Keep-alive watchdog for the AI Control Center.
  Relaunches server.py automatically if it stops responding on :8900.
  Usage:  powershell -ExecutionPolicy Bypass -File watchdog.ps1   (leave running)
#>
$ErrorActionPreference = 'SilentlyContinue'
$dir = 'C:\AI\agent-workspace\control-center'
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
Write-Host "Nova watchdog started — monitoring http://localhost:8900"
while ($true) {
  $up = $false
  try { Invoke-RestMethod 'http://localhost:8900/api/services' -TimeoutSec 4 | Out-Null; $up = $true } catch {}
  if (-not $up) {
    Write-Host ("[{0}] Control Center not responding — restarting…" -f (Get-Date -Format 'HH:mm:ss'))
    $py = (Get-Command python).Source
    Start-Process -WindowStyle Hidden $py -ArgumentList 'server.py' -WorkingDirectory $dir
    Start-Sleep 8
  }
  Start-Sleep 15
}
