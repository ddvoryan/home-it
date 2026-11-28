# home-it

Tooling for monitoring and automating home infrastructure, driven by Claude Code.

| Component | Status | Module |
|---|---|---|
| Synology NAS (DSM 7.x) - health, storage, backups, updates, Container Manager | ✅ inventory | `homeit.synology` |
| Plex Media Server | planned | - |

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# one-time site setup: see docs/synology.md
.\.venv\Scripts\python.exe -m homeit synology probe       # SSH + sudo + DSM API check
.\.venv\Scripts\python.exe -m homeit synology inventory   # full report
```

Reports and snapshots land in `~/.home-it/data/synology/` (`latest.md` is always the newest report).

## Recurring monitoring

```
 Task Scheduler (no AI, runs whenever the PC is on)        Claude scheduled tasks (desktop app open)
 ───────────────────────────────────────────────          ─────────────────────────────────────────
 hourly   synology check ──► state.json diff ──► alerts/pending.json ──► nas-alert-relay (2-hourly)
 Sun 4am  synology update-images ─(summary)──┘                │            push + email to owner, then --ack
                                                              └──────► nas-morning-digest (07:30)
                                                                        fresh inventory, emailed if crit/warn
```

- `check` alerts only on **new / escalated / worsened / resolved** critical and warning findings, keyed by a
  stable id, so a disk going from 90.5% to 90.6% full doesn't re-alert.
- `update-images` tags each running container's image `<repo>:homeit-prev`, runs one-shot Watchtower
  (config-preserving recreate), verifies health, **rolls back** failures (`--no-pull` recreate on the prev tag),
  then removes the `homeit-prev` rollback tags, which deletes each replaced image (like Watchtower's
  `--cleanup`, but only after the new image passed), and prunes dangling images. `--dry-run`, `--only NAME`
  and `--cleanup-previous` (cleanup only) are available.
- `usb-sync` (Sun 02:30, optional) rebuilds a single-version Hyper Backup task's folder list from
  `roots` / `exclude` / `protect` rules in site config. Those tasks can't use exclude rules, so new folders
  would otherwise never be backed up, and a renamed one fails the whole task.
- Snapshots: hourly ones are kept for 3 days, then the first of each day for 90 days.

## Design

- **Two channels to the NAS**: SSH (key-only, LAN-restricted key) for root-level reads such as SMART
  and `docker inspect`; the DSM Web API (the same API the DSM UI uses) for structured health, storage,
  Hyper Backup, update and Container Manager data.
- **TLS**: DSM's self-signed certificate is *pinned* by SHA-256 fingerprint instead of disabling verification.
- **Secrets**: the service-account password lives in the OS keyring (Windows Credential Manager / DPAPI).
  It is sent only in a POST body to DSM and over SSH stdin to `sudo -S`; never on a command line, in a URL, or on disk.
- **This repo is public**: hostnames, usernames, fingerprints, serials and snapshots stay out of git.
  Site config is `~/.home-it/config.toml` (schema: [`config.example.toml`](config.example.toml)).
- **Snapshots are redacted**: keys that look like tokens or passwords are masked, and container
  environment variables are reduced to their names.
