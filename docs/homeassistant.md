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

## Wall and phone panel (`ha deploy-panel`)

A custom panel (`panel_custom`) for a wall tablet in landscape and for phones. The layout is three
columns on screens 700px wide or more (no scrolling), and one scrolling column with full-screen sheets
on narrower screens. It switches to dark after sunset and light after sunrise. It runs inside HA's own
frontend, so it uses the viewer's login. The page holds no token.

| Piece | Where it lives |
|---|---|
| Generic code: `homeit/homeassistant/panel/home-panel.js`, `loader.js` | `<HA config>/www/home-panel/`, served at `/local/home-panel/` with **no login**, so it must never contain site details |
| Entity mapping: `~/.home-it/homeassistant/home_panel.json` (private) | `<HA config>/home_panel.yaml` (JSON is valid YAML). `configuration.yaml` includes it with `panel_custom: !include home_panel.yaml`, and HA sends it only to logged-in users |
| Helper scripts (thermostat fan timer, laser session start and end) | Generated from the mapping and saved through HA's script config API |

```powershell
.\.venv\Scripts\python.exe -m homeit ha deploy-panel --dry-run   # show what would change
.\.venv\Scripts\python.exe -m homeit ha deploy-panel             # upload code and scripts
.\.venv\Scripts\python.exe -m homeit ha deploy-panel --restart   # also restart HA when the YAML changed
```

- **Code changes:** reload the page; no restart is needed. `loader.js` never changes. It reads the build hash from
  `version.txt` without caching and imports `home-panel.js?v=<hash>`, so browser caches never serve a stale build.
  HA serves `/local/` with a 31-day cache, so `module_url` carries the loader's own hash as well. A change to the
  loader therefore changes the YAML and needs one restart, and devices that cached an older loader then fetch the new one.
- **Mapping changes:** restart HA, because `panel_custom` is read only at startup. The deploy runs HA's
  config check first and does not restart if the check fails.
- **Settings:** set `host_config_dir` in `[homeassistant]` to HA's `/config` folder as seen on the NAS.
  The upload goes over SSH with sudo. Files are installed with the folder's owner.

Mapping file shape (abridged, placeholders):

```json
{
  "panel": {"sidebar_title": "Home panel", "sidebar_icon": "mdi:view-dashboard-variant", "url_path": "home-panel"},
  "config": {
    "tou": {"utility": "<utility>", "name": "<rate plan>", "peak_start": 17, "peak_end": 20},
    "people": [{"entity": "person.<name>", "initials": "A", "color": "acc"}],
    "weather": {"forecast": "weather.home", "temp": "sensor.<station>_temp"},
    "energy": {"elec_to_date": "sensor.current_bill_electric_cost_to_date", "hourly_statistic": "opower:<id>"},
    "ev": {"power": "sensor.<charger>_power_output", "amps": "select.<charger>_charging_amperage_limit"},
    "front_door": {"camera": "camera.<doorbell>", "live": "camera.<doorbell>_live_view"},
    "security": {"mode": "alarm_control_panel.<location>", "mode_label": "Camera mode", "low_battery": 20,
      "cameras": [{"name": "Deck", "camera": "camera.<cam>", "motion": "binary_sensor.<cam>_motion",
        "last": "sensor.<cam>_last", "battery": "sensor.<cam>_battery", "connected": "binary_sensor.<cam>_connected"}]},
    "health": {"connectivity": ["binary_sensor.<device>_cloud_connection"]},
    "actions": [{"name": "Porch light", "icon": "lantern", "color": "solar", "entity": "switch.<porch>"}],
    "rooms": [{"name": "Living Room", "icon": "sofa", "kind": "climate", "climate": "climate.<thermostat>"}],
    "yard": [{"name": "Front yard", "standby": "switch.<controller>_in_standby_mode", "zones": []}],
    "calendars": [],
    "saver": {"start": "02:00", "end": "06:00", "idle_seconds": 120}
  }
}
```

**Room kinds:**

| Kind | What it shows and controls |
|---|---|
| `climate` | Mode, setpoints, eco preset, fan with timer |
| `appliance` | Home Connect state, plus a stop button |
| `switches` | Plain on/off switches |
| `workshop` | Outlets with power draw, plus a session start/end |
| `yard` | Irrigation controller: standby, rain delay and zones |

**Security:** with a `security` block, the Front door card becomes "Security". It adds a camera summary row
(last recording, offline cameras, batteries under `low_battery` %), and its sheet gets mode buttons and a grid of camera thumbnails.
Tapping a thumbnail opens HA's live view. `mode` is an `alarm_control_panel`, and the buttons change it with one tap.
`modes` overrides the default `[["disarmed","Off"],["armed_home","Home"],["armed_away","Away"]]`. While the mode is armed, motion
(the `motion` sensor, or a recording within `motion_alert_seconds`) raises an act-now alert. `last` may be an ISO timestamp or
hass-aarlo's `MM-DD HH:MM`. Every key except `name` and `camera` is optional.

**Second tap to confirm:** an item with `confirm_off: true` asks for a second tap before it switches off.
Starting the EV charger always asks for one.

**Colours** are the design guide's tokens: `solar`, `ok`, `home`, `grid`, `ev`, `acc`, `heat` and `alert`.
