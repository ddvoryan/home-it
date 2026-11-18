"""Weekly container image updates with health verification and automatic rollback.

Flow (all on the NAS, via SSH + sudo docker):
 1. Targets = running containers, minus watchtower itself and `update_exclude`.
 2. Tag each target's CURRENT image as <repo>:homeit-prev (the rollback point).
 3. One-shot watchtower (no --cleanup) pulls newer images and recreates only the
    containers whose image changed, preserving their full configuration.
 4. Verify every recreated container: running, not restarting, and healthy (or
    no healthcheck) after a grace period.
 5. Failed -> re-tag homeit-prev back onto the original tag and run watchtower
    with --no-pull, which recreates the container on the previous image.
 6. Prune dangling images (last week's rollback points). Record results and
    queue a summary alert for the Claude relay to report.
"""
from __future__ import annotations

import json
import shlex
import time
from datetime import datetime

from homeit import config, synology
from homeit.synology import inventory, monitor, ssh

WATCHTOWER = "containrrr/watchtower:latest"
PREV_TAG = "homeit-prev"


def _repo(ref: str) -> str | None:
    """'linuxserver/sonarr:latest' -> 'linuxserver/sonarr'; registry ports kept intact."""
    if "@" in ref:
        return None
    last = ref.rsplit("/", 1)[-1]
    return ref.rsplit(":", 1)[0] if ":" in last else ref


class _NAS:
    def __init__(self):
        self.cfg = config.synology()
        self.pw = synology.password(self.cfg)
        self.D = self.cfg.docker_bin

    def run(self, cmd: str, timeout: int = 300) -> ssh.Result:
        return ssh.run(self.cfg.ssh_alias, cmd, sudo_password=self.pw, timeout=timeout)

    def inspect(self, names: list[str] | None = None) -> dict[str, dict]:
        r = self.run(f"{self.D} inspect " + (" ".join(map(shlex.quote, names)) if names else f"$({self.D} ps -aq)"))
        # with several names, a missing one makes rc=1 but the others are still printed
        if not r.out.strip().startswith("["):
            raise RuntimeError(f"docker inspect failed: {r.err}")
        return {c["Name"].lstrip("/"): c for c in json.loads(r.out)}

    def watchtower(self, names: list[str], no_pull: bool = False) -> ssh.Result:
        args = ["--run-once", "--no-startup-message"] + (["--no-pull"] if no_pull else []) + names
        cmd = (f"{self.D} run --rm --name homeit-watchtower -v /var/run/docker.sock:/var/run/docker.sock "
               f"{WATCHTOWER} " + " ".join(map(shlex.quote, args)))
        return self.run(cmd, timeout=3600)


def _status(c: dict) -> str:
    st = c["State"]
    if st.get("Restarting") or st.get("Status") != "running":
        return "down"
    h = (st.get("Health") or {}).get("Status")
    return {"healthy": "ok", None: "ok", "starting": "starting"}.get(h, "unhealthy")


def _verify(nas: _NAS, names: list[str], grace: int = 90, timeout: int = 420) -> dict[str, str]:
    """Wait `grace`s, then poll until nothing is 'starting' (or timeout)."""
    if not names:
        return {}
    time.sleep(grace)
    deadline = time.time() + timeout
    while True:
        res = {n: _status(c) for n, c in nas.inspect(names).items()}
        if all(v != "starting" for v in res.values()) or time.time() > deadline:
            return res
        time.sleep(20)


def update_images(dry_run: bool = False, only: list[str] | None = None, force_rollback: bool = False) -> dict:
    nas = _NAS()
    exclude = set(getattr(nas.cfg, "update_exclude", ()) or ())
    t0 = datetime.now().astimezone()
    lock = monitor.lock_path()
    result = {"started": t0.isoformat(timespec="seconds"), "dry_run": dry_run,
              "updated": [], "rolled_back": [], "failed": [], "unchanged": [], "errors": []}
    try:
        lock.write_text(t0.isoformat(), encoding="utf-8")
        before = nas.inspect()
        targets = {n: c for n, c in before.items()
                   if c["State"].get("Status") == "running" and "watchtower" not in c["Config"]["Image"]
                   and n not in exclude and (not only or n in only)}
        result["targets"] = sorted(targets)
        if dry_run:
            upg = {f"{i['repository']}:{t}" for i in _cm_images() for t in i.get("tags", []) if i.get("upgradable")}
            result["flagged_by_container_manager"] = sorted(n for n, c in targets.items() if c["Config"]["Image"] in upg)
            return result

        # 2. rollback points
        for n, c in targets.items():
            repo = _repo(c["Config"]["Image"])
            if repo:
                r = nas.run(f"{nas.D} tag {c['Image']} {shlex.quote(repo + ':' + PREV_TAG)}")
                if not r.ok:
                    result["errors"].append(f"tag {n}: {r.err}")

        # 3. update
        r = nas.watchtower(sorted(targets))
        result["watchtower_log"] = (r.out + r.err)[-6000:]
        if not r.ok:
            result["errors"].append(f"watchtower exited {r.rc}")
        after = nas.inspect(sorted(targets))
        changed = [n for n in targets if n in after and after[n]["Image"] != targets[n]["Image"]]
        missing = [n for n in targets if n not in after]
        result["unchanged"] = sorted(set(targets) - set(changed) - set(missing))

        # 4. verify
        status = _verify(nas, changed)
        for n in missing:
            status[n] = "missing"
        if force_rollback:  # test hook: treat every changed container as failed
            status = {n: "forced" for n in changed}
        bad = [n for n, s in status.items() if s != "ok"]
        result["updated"] = sorted(n for n in changed if n not in bad)

        # 5. rollback
        if bad:
            for n in bad:
                ref = targets[n]["Config"]["Image"]
                repo = _repo(ref)
                nas.run(f"{nas.D} tag {shlex.quote(repo + ':' + PREV_TAG)} {shlex.quote(ref)}")
            r = nas.watchtower([n for n in bad if n not in missing], no_pull=True)
            result["rollback_log"] = (r.out + r.err)[-3000:]
            post = _verify(nas, [n for n in bad if n not in missing], grace=60)
            for n in bad:
                entry = {"name": n, "reason": status[n], "after_rollback": post.get(n, "missing")}
                (result["rolled_back"] if post.get(n) == "ok" else result["failed"]).append(entry)

        # 6. prune last week's rollback points (now dangling)
        r = nas.run(f"{nas.D} image prune -f")
        result["prune"] = r.out.strip().splitlines()[-1:] if r.ok else r.err
    except Exception as e:  # noqa: BLE001
        result["errors"].append(f"{type(e).__name__}: {e}")
    finally:
        lock.unlink(missing_ok=True)
        result["finished"] = datetime.now().astimezone().isoformat(timespec="seconds")
        if not dry_run:
            _record(result)
    return result


def _cm_images() -> list[dict]:
    with synology.dsm() as d:
        return d.call("SYNO.Docker.Image", "list", 1, limit=-1, offset=0, show_dsm=False).get("images", [])


def _record(res: dict) -> None:
    d = inventory.out_dir() / "updates"
    d.mkdir(exist_ok=True)
    (d / f"update-{datetime.now():%Y%m%d-%H%M%S}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    parts = []
    if res["updated"]:
        parts.append(f"updated {len(res['updated'])}: {', '.join(res['updated'])}")
    if res["rolled_back"]:
        parts.append("ROLLED BACK (new image unhealthy): " + ", ".join(f"{x['name']} ({x['reason']})" for x in res["rolled_back"]))
    if res["failed"]:
        parts.append("FAILED, still unhealthy after rollback: " + ", ".join(f"{x['name']} ({x['after_rollback']})" for x in res["failed"]))
    if res["errors"]:
        parts.append("errors: " + "; ".join(res["errors"]))
    if not parts:
        parts.append(f"no new images for {len(res.get('targets', []))} running containers")
    sev = "critical" if res["failed"] else "warning" if (res["rolled_back"] or res["errors"]) else "info"
    monitor.enqueue([{"ts": res["finished"], "kind": "update", "severity": sev, "area": "Containers",
                      "message": "Weekly image update: " + " | ".join(parts), "key": "image_update"}])


def main(dry_run: bool, only: list[str] | None, force_rollback: bool) -> None:
    res = update_images(dry_run=dry_run, only=only, force_rollback=force_rollback)
    res.pop("watchtower_log", None) if not dry_run else None
    print(json.dumps({k: v for k, v in res.items() if k != "rollback_log"}, indent=1))
