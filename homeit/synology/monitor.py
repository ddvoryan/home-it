"""Hourly change detection + alert queue.

`check` runs the inventory, compares findings with the previous check by their
stable keys and queues alerts for anything NEW, ESCALATED, WORSENED (e.g. SMART
counter went up) or RESOLVED. Only critical/warning findings alert. A Claude
scheduled task drains the queue (`alerts --json`, then `alerts --ack`) and
notifies the owner, so this module itself never talks to the outside world.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from homeit.synology import inventory

ALERTING = ("critical", "warning")
LOCK_MAX_AGE = timedelta(hours=2)


def _dir() -> Path:
    d = inventory.out_dir() / "alerts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _state_path() -> Path:
    return inventory.out_dir() / "state.json"


def lock_path() -> Path:
    return inventory.out_dir() / "update.lock"


def update_in_progress() -> bool:
    p = lock_path()
    return p.exists() and datetime.now() - datetime.fromtimestamp(p.stat().st_mtime) < LOCK_MAX_AGE


def _load(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _save(p: Path, obj) -> None:
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=1, default=str), encoding="utf-8")
    tmp.replace(p)


def enqueue(alerts: list[dict]) -> None:
    if not alerts:
        return
    p = _dir() / "pending.json"
    _save(p, _load(p, []) + alerts)


def diff(prev: dict[str, dict], cur: list[dict], now: str) -> list[dict]:
    out = []
    cur_by_key = {f["key"]: f for f in cur}
    for f in cur:
        if f["severity"] not in ALERTING:
            continue
        p = prev.get(f["key"])
        kind = None
        if p is None or p["severity"] not in ALERTING:
            kind = "new"
        elif inventory.SEV_ORDER[f["severity"]] < inventory.SEV_ORDER[p["severity"]]:
            kind = "escalated"
        elif f["area"] == "Disks" and isinstance(f.get("value"), (int, float)) and (p.get("value") or 0) < f["value"]:
            kind = "worsened"
        if kind:
            out.append({"ts": now, "kind": kind, **{k: f[k] for k in ("severity", "area", "message", "key")}})
    for key, p in prev.items():
        if p["severity"] in ALERTING and key not in cur_by_key:
            out.append({"ts": now, "kind": "resolved", "severity": "info", "area": p["area"],
                        "message": f"RESOLVED: {p['message']}", "key": key})
    return out


def prune(keep_hourly_days: int = 3, keep_daily_days: int = 90) -> int:
    """Hourly files for N days, then the first file of each day, deleted after M days."""
    d, now, removed = inventory.out_dir(), datetime.now(), 0
    for prefix in ("snapshot-", "report-"):
        seen_days = set()
        for f in sorted(d.glob(prefix + "*")):
            try:
                ts = datetime.strptime(f.stem[len(prefix):], "%Y%m%d-%H%M%S")
            except ValueError:
                continue
            age, day = now - ts, ts.date()
            first_of_day = day not in seen_days
            seen_days.add(day)
            if age > timedelta(days=keep_daily_days) or (age > timedelta(days=keep_hourly_days) and not first_of_day):
                f.unlink(missing_ok=True)
                removed += 1
    return removed


def check() -> int:
    """Returns the number of alerts queued."""
    state = _load(_state_path(), None)
    seeding = state is None
    state = state or {"findings": {}, "running": []}
    updating = update_in_progress()
    prev_running = None if updating or seeding else set(state.get("running", []))
    snap, rows, fnd, _ = inventory.run(prev_running)
    now = snap["collected_at"]

    if snap.get("fatal"):
        # NAS unreachable: alert once, but keep the previous findings so nothing "resolves".
        f = fnd[0]
        alerts = [] if "collect_failed" in state["findings"] else [
            {"ts": now, "kind": "new", **{k: f[k] for k in ("severity", "area", "message", "key")}}]
        state["findings"]["collect_failed"] = {k: f[k] for k in ("severity", "area", "message", "value")}
    else:
        alerts = [] if seeding else diff(state["findings"], fnd, now)
        state["findings"] = {f["key"]: {k: f[k] for k in ("severity", "area", "message", "value")} for f in fnd}
        state["running"] = sorted(r["name"] for r in rows if r["state"] == "running")
    state["last_check"] = now
    _save(_state_path(), state)
    enqueue(alerts)
    removed = prune()
    crit = sum(f["severity"] == "critical" for f in fnd)
    warn = sum(f["severity"] == "warning" for f in fnd)
    print(f"{now} check: {crit} critical, {warn} warning, {len(alerts)} new alert(s)"
          f"{' [seeded baseline]' if seeding else ''}{' [update in progress]' if updating else ''}"
          f"{f', pruned {removed} old files' if removed else ''}")
    for a in alerts:
        print(f"  ALERT {a['kind']:9} {a['severity']:8} {a['message']}")
    return len(alerts)


def alerts(ack: bool = False, as_json: bool = False, history_hours: int | None = None) -> None:
    d = _dir()
    if history_hours is not None:
        cutoff = datetime.now().astimezone() - timedelta(hours=history_hours)
        rows = []
        if (d / "history.jsonl").exists():
            for line in (d / "history.jsonl").read_text(encoding="utf-8").splitlines():
                a = json.loads(line)
                if datetime.fromisoformat(a["ts"]) >= cutoff:
                    rows.append(a)
        rows += _load(d / "pending.json", [])
        print(json.dumps(rows, indent=1) if as_json else "\n".join(f"{a['ts']} {a['kind']:9} {a['severity']:8} {a['message']}" for a in rows) or "(none)")
        return
    pending = _load(d / "pending.json", [])
    if ack:
        with (d / "history.jsonl").open("a", encoding="utf-8") as h:
            for a in pending:
                h.write(json.dumps({**a, "acked": datetime.now().astimezone().isoformat(timespec="seconds")}) + "\n")
        _save(d / "pending.json", [])
        print(f"acknowledged {len(pending)} alert(s)")
        return
    if as_json:
        print(json.dumps(pending, indent=1))
    else:
        print("\n".join(f"{a['ts']} {a['kind']:9} {a['severity']:8} {a['message']}" for a in pending) or "(no pending alerts)")
