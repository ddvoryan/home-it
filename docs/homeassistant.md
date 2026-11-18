# Home Assistant (container on the NAS)

The tooling talks to Home Assistant through its REST + WebSocket API with a
**long-lived access token (LLAT)** that belongs to a **dedicated HA user**, stored in the
OS keyring. Nothing about the site (URL, IPs, account names) belongs in this repo.

## One-time setup

1. **Create a service user in HA** (as the owner):
   Profile → turn on *Advanced mode* → Settings → People → **Users** tab → *Add user*.
   - Display name / username: `<svc-user>`; a long random password,
     kept in your password manager (it is only needed to mint tokens).
   - **Administrator: on.** Config entries, device/entity registries, repairs and
     config-flow progress are admin-only WebSocket commands.
   - **Can only log in from the local network: on.**
2. **Mint the token as that user**: open HA in a private window, log in as `<svc-user>`,
   Profile → **Security** → *Long-lived access tokens* → *Create token*, name it `home-it`.
   Copy it (HA shows it once).
3. **Store it** (hidden prompt; never paste it into chat, argv or a file):
   ```powershell
   .\.venv\Scripts\python.exe -m homeit ha set-token
   ```
4. Add the `[homeassistant]` section to `~/.home-it/config.toml` (see `config.example.toml`) and test:
   ```powershell
   .\.venv\Scripts\python.exe -m homeit ha probe
   ```

**Revoking:** delete the token under that user's Profile → Security, or deactivate the user.
Rotating = mint a new token and re-run `ha set-token`.

## Commands

| Command | What it does |
|---|---|
| `ha probe` | checks token + WebSocket auth, prints HA version and integration count |
| `ha inventory [--json] [--out FILE]` | integrations and their state, re-auth flows, repairs, devices, dashboards → `~/.home-it/data/homeassistant/latest.md` + JSON snapshot |

Both are read-only.

## Gotchas

- **No SSH tunnel.** DSM's sshd has `AllowTcpForwarding no` (and DSM updates reset
  sshd_config), so the API is reached directly on the LAN. If HA is plain http, the token
  crosses the LAN unencrypted; putting HA behind a TLS reverse proxy fixes that, then set
  `url` to the https address.
- **Bridge networking breaks discovery.** In a bridge-mode container mDNS/SSDP/DHCP
  discovery (Chromecast, HomeKit, Matter, many Wi-Fi devices) does not work, and HA sees
  LAN clients as the Docker gateway address. `network_mode: host` is the usual fix
  (HA then listens on 8123 directly).
- **Container install = no add-ons.** MQTT broker, Zigbee2MQTT, Matter server, etc. run as
  separate containers. USB radios must be passed through as devices; prefer
  network-attached (Ethernet/PoE) Zigbee/Thread coordinators on a NAS.
- **Integrations that log in to accounts with 2FA** (DSM, UniFi OS) fail forever once 2FA
  is turned on. Give HA its own local account without 2FA and least privilege.
