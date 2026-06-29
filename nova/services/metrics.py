# -*- coding: utf-8 -*-
"""System telemetry — CPU/RAM/disk via psutil, GPU via nvidia-smi. Temps are best-effort
(never faked: None → shown as N/A in the UI)."""
import time, subprocess
import psutil
from config import NVSMI

# Most recent metrics snapshot, published by the server's metrics_loop (set_last_metrics)
# and read by routes/insights (get_last_metrics) so they don't recompute every request.
_last_metrics = {}
def set_last_metrics(m):
    global _last_metrics
    _last_metrics = m or {}
def get_last_metrics():
    return _last_metrics

_cpu_temp = {"v": None, "t": 0}
def get_cpu_temp():
    """Best-effort CPU/system temperature from WMI thermal zone (cached 10s)."""
    now = time.time()
    if now - _cpu_temp["t"] < 10:
        return _cpu_temp["v"]
    _cpu_temp["t"] = now
    val = None
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature "
             "-ErrorAction Stop | Select-Object -First 1 -ExpandProperty CurrentTemperature)"],
            capture_output=True, text=True, timeout=6)
        s = (out.stdout or "").strip()
        if s.isdigit():
            c = int(s) / 10 - 273.15
            if 0 < c < 125: val = round(c, 1)
    except Exception:
        val = None
    _cpu_temp["v"] = val
    return val

def collect_metrics():
    cpu = psutil.cpu_percent(interval=None)
    vm = psutil.virtual_memory()
    try: disk = psutil.disk_usage("C:\\")
    except Exception: disk = None
    gpu = None
    try:
        out = subprocess.run(
            [NVSMI, "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,power.limit",
             "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=4)
        p = [x.strip() for x in out.stdout.strip().splitlines()[0].split(",")]
        gpu = {"name": p[0], "util": float(p[1]), "vram_used": float(p[2]), "vram_total": float(p[3]),
               "temp": float(p[4]), "power": float(p[5]), "power_limit": float(p[6])}
    except Exception: pass
    return {
        "type": "metrics", "ts": time.time(),
        "cpu": cpu, "cpu_cores": psutil.cpu_count(), "cpu_temp": get_cpu_temp(),
        "ram_used": round(vm.used / 1e9, 1), "ram_total": round(vm.total / 1e9, 1), "ram_pct": vm.percent,
        "disk_pct": disk.percent if disk else None,
        "disk_free": round(disk.free / 1e9, 1) if disk else None,
        "gpu": gpu,
    }
