"""Run commands on the NAS over OpenSSH (key auth, via the ~/.ssh/config alias).

BatchMode=yes guarantees we never hang on a password prompt. For root-level
reads (docker, smartctl, ...) the DSM account password is fed to `sudo -S` over
stdin of the encrypted SSH channel -- it is never placed on a command line, and
the NAS's sudoers file is left untouched (DSM updates reset it anyway).
"""
from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass


@dataclass
class Result:
    cmd: str
    rc: int
    out: str
    err: str

    @property
    def ok(self) -> bool:
        return self.rc == 0


def run(alias: str, cmd: str, *, sudo_password: str | None = None,
        timeout: int = 120) -> Result:
    remote = cmd
    stdin = None
    if sudo_password is not None:
        remote = f"sudo -S -p '' sh -c {shlex.quote(cmd)}"
        stdin = sudo_password + "\n"
    p = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", alias, remote],
        input=stdin, capture_output=True, text=True, timeout=timeout,
        encoding="utf-8", errors="replace",
        # no console window flashing up when run from pythonw / Task Scheduler
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return Result(cmd, p.returncode, p.stdout, p.stderr.strip())
