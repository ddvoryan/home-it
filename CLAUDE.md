# home-it: notes for Claude

## Hard rules
- **This repository is PUBLIC.** Never commit hostnames, IPs, usernames, emails, serial numbers,
  cert fingerprints, snapshots/reports, or anything from `~/.home-it/`. Use placeholders in docs.
  Grep the staged diff for these before every commit.
- Secrets only come from `homeit.secrets` (OS keyring). Never put them on a command line, in a URL,
  in env vars, or in files.
- Site config: `~/.home-it/config.toml`. Data: `~/.home-it/data/`. Not `%APPDATA%` (MSIX redirection, see docs/synology.md).

## Running
- Python venv at `.venv`: `.\.venv\Scripts\python.exe -m homeit <group> <cmd>`.
- Set `PYTHONIOENCODING=utf-8` when printing reports to a Windows console.
- NAS shell: `ssh nas '<cmd>'` (key auth, BatchMode). For root: `homeit.synology.ssh.run(..., sudo_password=...)`.

## Action policy on the NAS (agreed with the owner)
- Monitoring and inventory: always OK.
- **Routine actions OK without asking, report afterwards**: restart an unhealthy or crashed container,
  pull and recreate a container on an updated image.
- **Ask first**: DSM or package updates, changing DSM settings, storage, shares, users, Hyper Backup
  task edits, deleting containers, images, volumes or data, and anything touching Plex (a separate project).
