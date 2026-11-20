"""Keep a single-version Hyper Backup task's folder list in sync with the NAS.

Hyper Backup *single-version* tasks (Local folder & USB, single version) cannot use exclude
rules: they store an explicit list of folders. With a big media library that list goes stale:
new shows are never picked up, and a renamed or deleted folder makes the whole task fail with
`source_not_available`.

`synology usb-sync` rebuilds the list from rules in ~/.home-it/config.toml:

    [synology.usb_backup]
    task_name = "USB_Backup"
    roots     = ["/media", "/docker"]          # back these up...
    exclude   = ["/media/downloads", "/media/TV/Some Show"]   # ...except these
    protect   = ["/media/TV/Must Keep"]       # abort if one of these would not be backed up

A root is selected whole unless an excluded path lies inside it; then it is replaced by its
sub-folders (recursively), skipping the excluded ones. Loose files directly inside an expanded
folder cannot be selected by a folder list and are reported.

Safety: the task must be idle; every protected path must be covered; and a change that would
drop more than `max_drop_pct` of the folder entries (e.g. a share that isn't mounted) is refused
unless --force. The DSM config file is copied before every change.
"""
from __future__ import annotations

import json
import shlex
import time
from dataclasses import dataclass, field
from datetime import datetime

from homeit import config
from homeit.synology import dsm, inventory, monitor, password, ssh

CONF = "/var/packages/HyperBackup/etc/synobackup.conf"
KEEP_CONF_BACKUPS = 5


@dataclass
class Rules:
    task_name: str
    roots: list[str]
    exclude: list[str] = field(default_factory=list)
    protect: list[str] = field(default_factory=list)
    max_drop_pct: float = 10.0

    @classmethod
    def load(cls) -> "Rules":
        c = config.load().get("synology", {}).get("usb_backup")
        if not c:
            raise SystemExit(f"No [synology.usb_backup] section in {config.config_path()}; see config.example.toml")
        r = cls(**c)
        norm = lambda ps: [p.rstrip("/") for p in ps]
        r.roots, r.exclude, r.protect = norm(r.roots), norm(r.exclude), norm(r.protect)
        clash = [p for p in r.protect if any(p == e or p.startswith(e + "/") for e in r.exclude)]
        if clash:
            raise SystemExit(f"protected paths are also excluded: {clash}")
        return r


def _ls(cfg, pw, path: str) -> tuple[list[str], list[str]]:
    """(sub-folders, files) directly inside a share path like /media/TV."""
    q = shlex.quote("/volume1" + path)
    r = ssh.run(cfg.ssh_alias, f"[ -d {q} ] && find {q} -mindepth 1 -maxdepth 1 -printf '%y\\t%f\\n'",
                sudo_password=pw, timeout=300)
    if not r.ok:
        raise RuntimeError(f"cannot list {path}: rc={r.rc} {r.err.strip()}")
    dirs, files = [], []
    for line in r.out.splitlines():
        kind, _, name = line.partition("\t")
        if name.startswith(("@", "#")) or name in (".DS_Store", "Thumbs.db"):  # @eaDir, #recycle, OS clutter
            continue
        (dirs if kind == "d" else files).append(f"{path}/{name}")
    return sorted(dirs), sorted(files)


def desired(rules: Rules, ls) -> tuple[list[str], list[str], list[str]]:
    """Return (selection, loose_files_not_covered, excludes_not_found)."""
    sel, loose, seen = [], [], set()

    def walk(path: str):
        if path in rules.exclude:
            seen.add(path)
            return
        if any(e.startswith(path + "/") for e in rules.exclude):
            dirs, files = ls(path)
            loose.extend(files)
            for d in dirs:
                walk(d)
        else:
            sel.append(path)

    for root in rules.roots:
        walk(root)
    return sorted(set(sel)), loose, [e for e in rules.exclude if e not in seen]


def _covered(path: str, sel: list[str]) -> bool:
    return any(path == s or path.startswith(s + "/") for s in sel)


def _find_task(d, name: str) -> dict:
    for t in d.call("SYNO.Backup.Task", "list", 1)["task_list"]:
        if t["name"] == name:
            return t
    raise SystemExit(f"Hyper Backup task {name!r} not found")


def _backup_conf(cfg, pw) -> str:
    dst = f"{CONF}.homeit-{datetime.now():%Y%m%d-%H%M%S}"
    old = f"ls -1t {CONF}.homeit-* 2>/dev/null | tail -n +{KEEP_CONF_BACKUPS + 1} | xargs -r rm -f"
    r = ssh.run(cfg.ssh_alias, f"cp -p {CONF} {dst} && {old}", sudo_password=pw)
    if not r.ok:
        raise RuntimeError(f"could not back up {CONF}: {r.err.strip()}")
    return dst


def sync(dry_run: bool = False, force: bool = False) -> dict:
    cfg, rules = config.synology(), Rules.load()
    pw = password(cfg)
    res = {"started": datetime.now().astimezone().isoformat(timespec="seconds"), "task": rules.task_name,
           "dry_run": dry_run, "changed": False, "added": [], "removed": [], "loose_files": [],
           "stale_excludes": [], "aborted": None}
    sel, res["loose_files"], res["stale_excludes"] = desired(rules, lambda p: _ls(cfg, pw, p))
    res["count"] = len(sel)

    unprotected = [p for p in rules.protect if not _covered(p, sel)]
    if unprotected:
        res["aborted"] = f"protected folders would not be backed up (missing on the NAS?): {unprotected}"
    with dsm(cfg, session_name="webui") as d:      # DSM refuses task edits from other session names (error 119)
        task = _find_task(d, rules.task_name)
        cur = [f["folderPath"] for f in d.call("SYNO.Backup.Task", "get", 1, task_id=task["task_id"],
                                                additional=["source"])["source"]["file_list"]]
        res["added"] = sorted(set(sel) - set(cur))
        res["removed"] = sorted(set(cur) - set(sel))
        res["previous_count"] = len(cur)
        drop = 100 * len(res["removed"]) / max(len(cur), 1)
        if not res["aborted"] and drop > rules.max_drop_pct and not force:
            res["aborted"] = (f"would remove {len(res['removed'])} of {len(cur)} entries ({drop:.0f}% > "
                              f"{rules.max_drop_pct:.0f}%); check the shares are mounted, then rerun with --force")
        pending = bool(res["added"] or res["removed"])
        if not res["aborted"] and pending and not dry_run and task.get("status") not in ("none", None):
            res["aborted"] = f"task is busy ({task['status']}); will retry next run"
        if not res["aborted"] and pending and not dry_run:
            res["conf_backup"] = _backup_conf(cfg, pw)
            d.call("SYNO.Backup.Task", "set", 1, task_id=task["task_id"], repo_id=task["repo_id"],
                   target_type=task["target_type"], transfer_type=task["transfer_type"],
                   source={"file_list": sel, "app_list": [], "app_config": []})
            time.sleep(2)
            now = d.call("SYNO.Backup.Task", "get", 1, task_id=task["task_id"], additional=["source"])["source"]["file_list"]
            got = sorted(f["folderPath"] for f in now)
            if got != sel:
                raise RuntimeError(f"task folder list did not update as expected ({len(got)} vs {len(sel)} entries)")
            res["changed"] = True
    res["finished"] = datetime.now().astimezone().isoformat(timespec="seconds")
    if not dry_run:
        _record(res)
    return res


def _record(res: dict) -> None:
    d = inventory.out_dir() / "usb-sync"
    d.mkdir(exist_ok=True)
    (d / f"usb-sync-{datetime.now():%Y%m%d-%H%M%S}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    if res["aborted"]:
        sev = "critical" if "protected" in res["aborted"] else "warning"
        msg = f"{res['task']} folder sync skipped: {res['aborted']}"
    elif res["changed"]:
        sev = "info"
        names = lambda ps: ", ".join(p.rsplit("/", 1)[-1] for p in ps[:8]) + (" ..." if len(ps) > 8 else "")
        parts = [f"added {len(res['added'])}" + (f" ({names(res['added'])})" if res["added"] else ""),
                 f"removed {len(res['removed'])}" + (f" ({names(res['removed'])})" if res["removed"] else "")]
        msg = f"{res['task']} folder list updated: " + "; ".join(parts)
    else:
        return
    if res["stale_excludes"]:
        msg += f" | excludes no longer on the NAS: {', '.join(res['stale_excludes'])}"
    monitor.enqueue([{"ts": res["finished"], "kind": "usb_sync", "severity": sev, "area": "Backup",
                      "message": msg, "key": "usb_sync"}])


def main(dry_run: bool, force: bool) -> None:
    res = sync(dry_run=dry_run, force=force)
    short = dict(res)
    for k in ("added", "removed"):
        short[k] = res[k] if len(res[k]) <= 30 else res[k][:30] + [f"... {len(res[k]) - 30} more"]
    print(json.dumps(short, indent=1))
    if res["aborted"]:
        raise SystemExit(2)
