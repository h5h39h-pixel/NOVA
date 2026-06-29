# -*- coding: utf-8 -*-
"""
Process ownership — a Windows Job Object so child processes (PowerShell, training
python, Playwright, ffmpeg) are assigned to the server and cannot outlive it
(KILL_ON_JOB_CLOSE). Pure infrastructure: depends only on the stdlib + logging.
"""
import os, base64, logging
log = logging.getLogger("nova")


def ps_args(command):
    """Run a PowerShell command with bulletproof UTF-8 in/out (handles Arabic, box chars,
    and any quoting) by passing it as a UTF-16LE base64 -EncodedCommand."""
    setup = ("[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
             "$OutputEncoding=[System.Text.Encoding]::UTF8; "
             "$ProgressPreference='SilentlyContinue'; "
             "$ErrorActionPreference='Continue'; "
             "try{chcp 65001 > $null}catch{}; ")
    # Run inside a script block, merge the error stream, and pipe through
    # Out-String -Stream so errors render as plain readable text (no CLIXML)
    # while output still streams line-by-line.
    wrapped = setup + "& {\n" + command + "\n} 2>&1 | Out-String -Stream"
    enc = base64.b64encode(wrapped.encode("utf-16-le")).decode("ascii")
    return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", enc]


def _q(s):
    """Quote a single argument for a PowerShell command line (leaves bare flags alone)."""
    s = str(s)
    return s if s.startswith("-") and " " not in s else '"' + s.replace('"', '`"') + '"'


_JOB = None

def init_job_object():
    global _JOB
    if os.name != "nt":
        return
    try:
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)

        class BASIC(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.POINTER(ctypes.c_ulong)), ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [("r", ctypes.c_uint64), ("w", ctypes.c_uint64), ("o", ctypes.c_uint64),
                        ("rt", ctypes.c_uint64), ("wt", ctypes.c_uint64), ("ot", ctypes.c_uint64)]
        class EXT(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BASIC), ("IoInfo", IO), ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]
        k32.CreateJobObjectW.restype = wintypes.HANDLE
        h = k32.CreateJobObjectW(None, None)
        if not h:
            return
        info = EXT()
        info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        k32.SetInformationJobObject(h, 9, ctypes.byref(info), ctypes.sizeof(info))  # ExtendedLimitInformation
        _JOB = (k32, h)
        log.info("Job Object created — child processes will not orphan")
    except Exception as e:
        log.warning(f"Job Object unavailable: {e}")

def assign_to_job(pid):
    if not _JOB or not pid:
        return
    try:
        k32, h = _JOB
        hp = k32.OpenProcess(0x0100 | 0x0001, False, int(pid))  # SET_QUOTA | TERMINATE
        if hp:
            k32.AssignProcessToJobObject(h, hp)
            k32.CloseHandle(hp)
    except Exception:
        pass
