# -*- coding: utf-8 -*-
"""Command safety — the single, shared destructive-command denylist used by both the Terminal
(/api/exec) and the agent's run_command. Regex- and command-boundary-aware: it matches dangerous
*verbs* only at a real command boundary (start, or after ; & | newline or a backtick) to cut false
positives like `echo "format my report"`, while still catching piped deletes
(`Get-ChildItem | Remove-Item -Force`) and flag variants/aliases.

It is a safety speed-bump, NOT a sandbox — on localhost the Terminal confirms and proceeds; the
agent blocks unless run in full-access mode. Stdlib-only (bottom layer, no nova deps)."""
import re

# a destructive verb counts only at a command boundary
_B = r"(?:^|[\n;&|`]\s*)"

_PATTERNS = [
    # disk / partition / filesystem
    # `format(?!-)` matches disk `format c:` but NOT PowerShell formatting cmdlets (format-table/list/wide)
    (re.compile(_B + r"(format(?!-)|format-volume|diskpart|mkfs|clear-disk|initialize-disk|remove-partition|clear-volume)\b", re.I),
     "disk/partition/format operation"),
    # recursive or forced delete (PowerShell + cmd, incl. aliases rm/ri/rd/rmdir/del/erase and pipes)
    (re.compile(_B + r"(remove-item|ri|rm|rmdir|rd|del|erase)\b[^\n;]*?(\s-(r|rf|fr|recurse|force|fo)\b|\s/s\b|\s/q\b|\*\.\*)", re.I),
     "recursive/forced file deletion"),
    # -recurse + -force together, in any order, anywhere
    (re.compile(r"-recurse\b[^\n]*-force\b|-force\b[^\n]*-recurse\b", re.I),
     "recursive force deletion"),
    # power / session
    (re.compile(_B + r"(shutdown|stop-computer|restart-computer|logoff)\b", re.I),
     "shutdown/restart"),
    # registry destruction
    (re.compile(r"\breg\b\s+delete\b|\bregedit\b\s+/s\b", re.I), "registry delete/import"),
    (re.compile(_B + r"remove-item\b[^\n;]*hk(lm|cu|cr|u|cc):", re.I), "registry key delete"),
    # shadow copies / backups
    (re.compile(r"\b(vssadmin|wbadmin)\b[^\n]*\bdelete\b", re.I), "delete shadow copies / backups"),
    # secure wipe
    (re.compile(r"\bcipher\b\s+/w|\bsdelete\b", re.I), "secure disk wipe"),
    # boot configuration
    (re.compile(r"\b(bcdedit|bootrec)\b", re.I), "boot configuration change"),
    # scheduled-task / service teardown of everything
    (re.compile(r"\bschtasks\b[^\n]*/delete\b[^\n]*/tn\s*\*|\bunregister-scheduledtask\b", re.I),
     "scheduled-task deletion"),
]


def danger_reason(cmd):
    """Return a short reason string if the command looks destructive, else None."""
    s = cmd or ""
    for rx, why in _PATTERNS:
        if rx.search(s):
            return why
    return None


def is_dangerous(cmd):
    """True if the command matches a destructive pattern."""
    return danger_reason(cmd) is not None


# ─── credential-store read denylist (shared) ────────────────────────────────
# Paths that must never be read by any feature (file read, KB/folder ingest, agent understand).
# Same list the agent enforces; centralized here so every reader uses one source of truth.
DENY_READ = (".ssh", ".aws", ".env", "credentials", "login data", "id_rsa", "id_ed25519",
             "ntuser.dat", "\\.git\\config", ".npmrc", ".pypirc")


def is_credential_path(path) -> bool:
    """True if `path` points into a credential/secret store and must not be read."""
    return any(d in str(path).lower() for d in DENY_READ)
