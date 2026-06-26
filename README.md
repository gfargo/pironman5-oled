# 🖥️ Pironman5 OLED Pages

Custom OLED display pages for the [Sunfounder Pironman5 MAX](https://www.sunfounder.com/products/pironman-5-max) case — an orchestrator-pattern replacement for the default page rotation, with homelab service integrations and animated screensavers.

![Pironman5 MAX](https://img.shields.io/badge/hardware-Pironman5%20MAX-orange)
![Pi 5](https://img.shields.io/badge/platform-Raspberry%20Pi%205-red)
![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)

---

## What it does

Replaces the Pironman5's default OLED page rotation (flat timer-based list) with a single **orchestrator** page that manages a sophisticated display flow:

```
info page (12s) → screensaver (45s) → info page (12s) → screensaver (45s) → ...
```

Features:
- **15 info pages** rotating sequentially (system vitals, Docker health, network, NVMe, backups, sprint progress, portfolio, weather, and more)
- **14 animated screensavers** randomly selected between info pages (Matrix rain, Game of Life, starfield, spirograph, ocean waves, and more)
- **Alert mode** — interrupts rotation when `/tmp/oled_alert` exists (health monitor writes this)
- **Button controls** — short press = skip to next, pause via file flag
- **Service integrations** — reads from Plane, Ghostfolio, Actual Budget, OctoPrint, GitHub (via API tokens)
- **Graceful degradation** — pages that crash skip instead of freezing the display; pages without configured tokens show "not configured"

## Info Pages

| Page | What it shows |
|------|---------------|
| Clock | Current time + date |
| CPU & Memory | Usage bars + load averages |
| Docker Health | Container count + status summary |
| Temperature | CPU + NVMe temps with trend |
| Network | Tailscale peers + connectivity |
| NVMe Health | Wear level, temp, power hours |
| Backup Status | Latest backup age + size + health |
| Sprint Board | Current Plane cycle progress |
| Portfolio Ticker | Ghostfolio portfolio value |
| Budget Burn | Actual Budget monthly spend rate |
| Plane Stats | Open items, overdue count |
| Weather | Current conditions (if configured) |
| OctoPrint | Print progress + ETA |
| GitHub Activity | Recent notifications |
| Mix | Combined overview (CPU/RAM/disk/temp) |

## Screensavers

Matrix Rain · Game of Life · Starfield · Spirograph · Ocean Waves · Perlin Terrain · Particles · Pendulum Wave · Fractal Tree · Lissajous · DVD Bounce · Binary Clock · Sine Wave · Uptime Counter

## Installation

**Prerequisites:** Pironman5 MAX case installed with the official [pironman5 software](https://github.com/sunfounder/pironman5) (the `max` branch).

```bash
# Clone to your Pi
git clone https://github.com/gfargo/pironman5-oled.git ~/pironman5-oled

# Deploy (installs pages into the pironman5 venv + restarts service)
sudo bash ~/pironman5-oled/deploy.sh
```

That's it. The OLED will start showing the orchestrator flow within seconds.

## Updating

```bash
cd ~/pironman5-oled && git pull && sudo bash deploy.sh
```

## Configuration

### Secrets (for authenticated pages)

Create `/opt/pironman5/oled-secrets.env` with tokens for service integrations:

```env
# Ghostfolio — portfolio ticker page
GHOSTFOLIO_TOKEN=your-ghostfolio-access-token

# Actual Budget — budget burn rate page  
ACTUAL_PASSWORD=your-actual-budget-password

# Plane — sprint board + stats pages
PLANE_API_TOKEN=your-plane-api-key

# GitHub — activity page
GITHUB_TOKEN=ghp_your_github_pat

# OctoPrint — printer status page
OCTOPRINT_API_KEY=your-octoprint-api-key
```

Pages degrade gracefully without tokens — they show "not configured" instead of crashing.

### Timing

Edit the constants in `pages/orchestrator.py`:
- `INFO_DURATION = 12` — seconds per info page
- `SCREENSAVER_DURATION = 45` — seconds per screensaver
- `ALERT_DURATION = 5` — alert display cycle

### Disabling pages

Remove unwanted page imports from the `self.info_pages` list in `pages/orchestrator.py`.

## How it works

### The Orchestrator Pattern

The default pironman5 OLED system uses a flat page list with a timer-based rotation. This doesn't support:
- Mixed timing (info pages need 12s, screensavers need 45s)
- Interleaved content types
- Priority interrupts (alerts)

The solution: register a **single "orchestrator" page** that internally manages the display flow. Pironman5 sees one page and never rotates. The orchestrator runs a state machine:

```
┌─────────┐    12s elapsed    ┌──────────────┐    45s elapsed    ┌─────────┐
│  INFO   │──────────────────▶│ SCREENSAVER  │──────────────────▶│  INFO   │
│ (next)  │◀─────────────────┤│  (random)    │                   │ (next)  │
└─────────┘    skip button    └──────────────┘                   └─────────┘
     │                                                                 │
     │         /tmp/oled_alert exists                                  │
     ▼                                                                 ▼
┌─────────┐                                                      ┌─────────┐
│  ALERT  │──────── alert file removed ─────────────────────────▶│  INFO   │
└─────────┘                                                      └─────────┘
```

The pironman5 config:
```json
{
    "oled_pages": ["orchestrator"],
    "page_rotate_interval": 9999
}
```

### Button Controls

- **Short press** — skip to next (creates `/tmp/oled_skip` file flag)
- **Pause** — creates `/tmp/oled_paused` file flag (small dot indicator in corner)

### Alert Mode

The health monitor (`health_monitor.py`) runs via cron every 5 minutes. When it detects an unhealthy condition (high temp, disk full, containers down), it writes `/tmp/oled_alert`. The orchestrator immediately switches to the alert page until the condition resolves.

### RGB Status LEDs

The `rgb_status.py` script (cron every 1 minute) sets the case LEDs based on system health:
- 🟢 Green — all healthy
- 🟡 Amber — warning (high temp, disk >80%)
- 🔴 Red — critical (containers down, disk >95%, temp >80°C)

## Cron Jobs

Add to the Pi's crontab (`crontab -e`):

```cron
# Health monitor — triggers OLED alerts
*/5 * * * * /opt/pironman5/venv/bin/python3 /home/gfargo/pironman5-oled/pages/health_monitor.py

# RGB status — LED color reflects system health
* * * * * /opt/pironman5/venv/bin/python3 /home/gfargo/pironman5-oled/pages/rgb_status.py
```

## Project Structure

```
pironman5-oled/
├── README.md
├── LICENSE
├── deploy.sh              # One-command install/update
├── oled_addon.py          # Reference: the OLEDAddon class (pironman5 plugin system)
└── pages/
    ├── __init__.py        # Page registry
    ├── orchestrator.py    # The main orchestrator (state machine)
    ├── alert_page.py      # Alert display
    ├── button_handler.py  # Button event handling
    ├── health_monitor.py  # Cron: writes /tmp/oled_alert on unhealthy state
    ├── rgb_status.py      # Cron: sets LED color based on health
    ├── clock.py           # Info: time + date
    ├── cpu_memory.py      # Info: CPU + RAM bars
    ├── docker_health.py   # Info: container count + status
    ├── temperature.py     # Info: CPU + NVMe temps
    ├── network_status.py  # Info: Tailscale peers
    ├── nvme_health.py     # Info: NVMe wear + temp
    ├── backup_status.py   # Info: latest backup health
    ├── sprint_board.py    # Info: Plane cycle progress (needs token)
    ├── portfolio_ticker.py # Info: Ghostfolio value (needs token)
    ├── budget_burn.py     # Info: Actual Budget burn rate (needs token)
    ├── plane_stats.py     # Info: Plane open items (needs token)
    ├── weather.py         # Info: current weather
    ├── octoprint_status.py # Info: print progress (needs token)
    ├── github_activity.py # Info: notifications (needs token)
    ├── mix.py             # Info: combined overview
    ├── disks.py           # Info: disk usage
    ├── performance.py     # Info: system performance
    ├── ips.py             # Info: IP addresses
    └── screensavers/
        ├── __init__.py    # ALL_SCREENSAVERS registry
        ├── matrix_rain.py
        ├── game_of_life.py
        ├── starfield.py
        ├── spirograph.py
        ├── ocean_waves.py
        ├── perlin_terrain.py
        ├── particles.py
        ├── pendulum_wave.py
        ├── fractal_tree.py
        ├── lissajous.py
        ├── dvd_bounce.py
        ├── binary_clock.py
        ├── sine_wave.py
        └── uptime_counter.py
```

## Hardware

- **Case:** Sunfounder Pironman5 MAX
- **Display:** SSD1306 128×64 OLED (I2C)
- **Computer:** Raspberry Pi 5 (any RAM variant)
- **LEDs:** 4× WS2812B RGB (addressable via GPIO)

## Credits

Built on top of the excellent [pironman5](https://github.com/sunfounder/pironman5) software by Sunfounder. The orchestrator pattern and custom pages are original work.

## License

MIT — see [LICENSE](./LICENSE).
