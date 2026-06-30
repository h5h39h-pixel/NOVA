# -*- coding: utf-8 -*-
"""Unit tests — nova/core/safety (shared destructive-command denylist, SEC-2)."""
import pytest
from nova.core.safety import is_dangerous, danger_reason

DANGEROUS = [
    "format c:",
    "Format-Volume -DriveLetter D",
    "Remove-Item -Recurse -Force C:\\stuff",
    "rm -rf /tmp/x",
    "del /s /q C:\\temp",
    "rd /s C:\\x",
    "Get-ChildItem C:\\logs -Recurse | Remove-Item -Force",   # piped delete
    "shutdown /s /t 0",
    "Stop-Computer",
    "reg delete HKLM\\Software\\Foo /f",
    "vssadmin delete shadows /all",
    "cipher /w:C",
    "diskpart",
    "bcdedit /set foo bar",
    "ri C:\\x -fo",                                            # alias + -force short
]

SAFE = [
    "echo hello",
    'echo "format my report and rm the draft"',               # destructive words inside an echo string
    "Get-Process | Sort-Object CPU",
    "dir C:\\Users",
    "Remove-Item C:\\x\\one.txt",                             # single-file delete, no -recurse/-force
    "ls -la",
    "python train.py",
    "Get-ChildItem -Recurse",                                 # listing, no delete verb
    "format-table",                                            # PowerShell formatting cmdlet, not disk format
]


@pytest.mark.parametrize("cmd", DANGEROUS)
def test_dangerous(cmd):
    assert is_dangerous(cmd), f"should be flagged: {cmd!r}"
    assert danger_reason(cmd)


@pytest.mark.parametrize("cmd", SAFE)
def test_safe(cmd):
    assert not is_dangerous(cmd), f"false positive: {cmd!r} -> {danger_reason(cmd)}"
