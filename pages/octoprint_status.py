"""OctoPrint Status — printer state, progress, temps from watch's OctoPrint API."""
import json
import urllib.request
import time
from pm_auto.libs.oled_page import OLEDPage
from pm_auto.libs.utils import get_font

font = get_font('UbuntuSans-Regular.ttf')

# OctoPrint API on watch (reachable via Tailscale)
OCTOPRINT_URL = "http://watch:5055"


class PageOctoprintStatus(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = None
        self._tick = 0
        self._last_fetch = 0

    def _fetch_status(self):
        now = time.time()
        # Refresh every 30 seconds
        if self._cache and (now - self._last_fetch) < 30:
            return self._cache

        status = {'state': 'offline', 'progress': 0, 'time_left': '',
                  'bed_temp': 0, 'tool_temp': 0, 'file': ''}

        try:
            # Printer state
            req = urllib.request.Request(
                f"{OCTOPRINT_URL}/api/printer",
                headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                temps = data.get('temperature', {})
                status['bed_temp'] = int(temps.get('bed', {}).get('actual', 0))
                status['tool_temp'] = int(temps.get('tool0', {}).get('actual', 0))
                state_flags = data.get('state', {}).get('flags', {})
                if state_flags.get('printing'):
                    status['state'] = 'printing'
                elif state_flags.get('ready'):
                    status['state'] = 'ready'
                elif state_flags.get('error'):
                    status['state'] = 'error'
                else:
                    status['state'] = 'idle'
        except urllib.error.HTTPError as e:
            if e.code == 409:
                status['state'] = 'disconnected'
            else:
                status['state'] = 'offline'
        except Exception:
            status['state'] = 'offline'

        # Job progress (if printing)
        if status['state'] == 'printing':
            try:
                req = urllib.request.Request(
                    f"{OCTOPRINT_URL}/api/job",
                    headers={'Accept': 'application/json'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    job = json.loads(resp.read())
                    progress = job.get('progress', {})
                    status['progress'] = int(progress.get('completion', 0) or 0)
                    time_left = progress.get('printTimeLeft', 0) or 0
                    if time_left > 3600:
                        status['time_left'] = f"{time_left // 3600}h {(time_left % 3600) // 60}m"
                    elif time_left > 60:
                        status['time_left'] = f"{time_left // 60}m"
                    else:
                        status['time_left'] = f"{time_left}s"
                    status['file'] = job.get('job', {}).get('file', {}).get('name', '')[:18]
            except Exception:
                pass

        self._cache = status
        self._last_fetch = now
        return self._cache

    def main(self, oled, data, config):
        s = self._fetch_status()
        self._tick += 1
        oled.clear()

        # Header
        state_icon = {"printing": "*", "ready": ".", "idle": "-",
                      "error": "!", "offline": "x", "disconnected": "?"}.get(s['state'], '?')
        oled.draw_text('3D PRINT', 0, 0, size=10, font_path=font)
        oled.draw_text(state_icon, 118, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        if s['state'] == 'printing':
            # File name
            oled.draw_text(s['file'], 0, 14, size=9, font_path=font)
            # Progress bar
            bar_y = 26
            oled.draw.line([(0, bar_y), (100, bar_y)], fill=1)
            oled.draw.line([(0, bar_y + 6), (100, bar_y + 6)], fill=1)
            fill = int(s['progress'])
            for y in range(bar_y + 1, bar_y + 6):
                oled.draw.line([(0, y), (fill, y)], fill=1)
            oled.draw_text(f"{s['progress']}%", 103, bar_y - 1, size=9, font_path=font)
            # Time remaining
            oled.draw_text(f"ETA: {s['time_left']}", 0, 36, size=10, font_path=font)
            # Temps
            oled.draw_text(f"Nozzle:{s['tool_temp']}C Bed:{s['bed_temp']}C", 0, 50, size=9, font_path=font)
        elif s['state'] == 'offline':
            oled.draw_text("OctoPrint", 20, 22, size=12, font_path=font)
            oled.draw_text("unreachable", 22, 38, size=11, font_path=font)
        elif s['state'] == 'disconnected':
            oled.draw_text("Printer", 30, 22, size=12, font_path=font)
            oled.draw_text("not connected", 14, 38, size=11, font_path=font)
        else:
            oled.draw_text(f"State: {s['state']}", 0, 18, size=11, font_path=font)
            if s['tool_temp'] > 0 or s['bed_temp'] > 0:
                oled.draw_text(f"Nozzle: {s['tool_temp']}C", 0, 34, size=11, font_path=font)
                oled.draw_text(f"Bed:    {s['bed_temp']}C", 0, 48, size=11, font_path=font)
            else:
                oled.draw_text("Printer idle", 20, 38, size=11, font_path=font)

        oled.display()
