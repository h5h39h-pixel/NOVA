# -*- coding: utf-8 -*-
"""System telemetry — CPU/RAM/disk via psutil, GPU via nvidia-smi. Temps are best-effort
(never faked: None → shown as N/A in the UI)."""
import time, subprocess
import psutil
from config import NVSMI
from nova.core.db import db

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


def record_history(m, keep=2880):
    """Persist a metrics sample to metrics_history (called ~every 30s), pruned to `keep` rows
    (≈24h at 30s spacing). Cheap trend storage for the System Monitor."""
    g = m.get("gpu") or {}
    c = db()
    c.execute("INSERT INTO metrics_history(ts,cpu,ram,gpu_util,vram_used,vram_total,gpu_temp) VALUES(?,?,?,?,?,?,?)",
              (m.get("ts"), m.get("cpu"), m.get("ram_pct"), g.get("util"), g.get("vram_used"),
               g.get("vram_total"), g.get("temp")))
    c.execute("DELETE FROM metrics_history WHERE id NOT IN "
              "(SELECT id FROM metrics_history ORDER BY id DESC LIMIT ?)", (keep,))
    c.commit(); c.close()


def history(limit=240):
    c = db()
    rows = [dict(r) for r in c.execute(
        "SELECT ts,cpu,ram,gpu_util,vram_used,vram_total,gpu_temp FROM metrics_history "
        "ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
    c.close()
    return list(reversed(rows))
