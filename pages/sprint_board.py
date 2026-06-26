"""Sprint Board — Plane current cycle progress + countdown."""
import json
import urllib.request
import time
import os
from datetime import datetime
from pm_auto.libs.oled_page import OLEDPage
from pm_auto.libs.utils import get_font

font = get_font('UbuntuSans-Regular.ttf')

# Plane API (internal, on same host)
PLANE_API_URL = os.environ.get('PLANE_API_URL', 'http://localhost:8080')
PLANE_API_TOKEN = ''  # loaded from secrets

SECRETS_FILE = '/opt/pironman5/oled-secrets.env'
SCREEN_W = 128


def _load_secret(key):
    """Load a secret from the env file."""
    val = os.environ.get(key, '')
    if val:
        return val
    try:
        with open(SECRETS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f'{key}='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return ''


class PageSprintBoard(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = None
        self._tick = 0
        self._last_fetch = 0
        self._token = _load_secret('PLANE_API_TOKEN')
        self._workspace = _load_secret('PLANE_WORKSPACE_SLUG') or 'gfargo'
        self._project_id = _load_secret('PLANE_PROJECT_ID') or 'cf7d9230-4a35-4161-8556-ba56a0ce7192'

    def _fetch_sprint(self):
        now = time.time()
        # Refresh every 5 minutes
        if self._cache and (now - self._last_fetch) < 300:
            return self._cache

        data = {'name': '?', 'done': 0, 'total': 0, 'pct': 0, 'days_left': '?', 'end_date': ''}

        if not self._token:
            data['error'] = 'no token'
            self._cache = data
            return data

        try:
            # Get active cycles for the project
            url = f"{PLANE_API_URL}/api/v1/workspaces/{self._workspace}/projects/{self._project_id}/cycles/"
            req = urllib.request.Request(url, headers={
                'X-API-Key': self._token,
                'Accept': 'application/json'
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                cycles = json.loads(resp.read())
                results = cycles.get('results', cycles) if isinstance(cycles, dict) else cycles

                # Find active cycle (current date within start/end)
                today = datetime.now().strftime('%Y-%m-%d')
                active_cycle = None
                for cycle in (results if isinstance(results, list) else []):
                    start = cycle.get('start_date', '')
                    end = cycle.get('end_date', '')
                    if start and end and start <= today <= end:
                        active_cycle = cycle
                        break

                if not active_cycle and results:
                    # Fallback: use the most recent cycle
                    active_cycle = results[-1] if isinstance(results, list) else None

                if active_cycle:
                    data['name'] = (active_cycle.get('name', '?'))[:16]
                    data['end_date'] = active_cycle.get('end_date', '')

                    # Calculate days remaining
                    if data['end_date']:
                        try:
                            end_dt = datetime.strptime(data['end_date'], '%Y-%m-%d')
                            delta = (end_dt - datetime.now()).days
                            data['days_left'] = max(0, delta)
                        except ValueError:
                            data['days_left'] = '?'

                    # Get issue counts from cycle detail
                    total = active_cycle.get('total_issues', 0)
                    completed = active_cycle.get('completed_issues', 0)
                    data['total'] = total
                    data['done'] = completed
                    data['pct'] = int(completed * 100 / total) if total > 0 else 0

                    self._last_fetch = now
                else:
                    data['error'] = 'no active cycle'

        except Exception as e:
            data['error'] = str(e)[:25]

        self._cache = data
        return data

    def main(self, oled, data_arg, config):
        s = self._fetch_sprint()
        self._tick += 1
        oled.clear()

        # Header
        oled.draw_text('SPRINT', 0, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        if s.get('error') == 'no token':
            oled.draw_text("Plane token", 16, 22, size=12, font_path=font)
            oled.draw_text("not configured", 10, 38, size=11, font_path=font)
        elif s.get('error') == 'no active cycle':
            oled.draw_text("No active", 22, 22, size=12, font_path=font)
            oled.draw_text("sprint/cycle", 16, 38, size=12, font_path=font)
        elif s.get('error'):
            oled.draw_text("Plane API", 22, 22, size=12, font_path=font)
            oled.draw_text("unreachable", 20, 38, size=11, font_path=font)
        else:
            # Cycle name
            oled.draw_text(s['name'], 0, 14, size=11, font_path=font)

            # Progress: X/Y done
            oled.draw_text(f"{s['done']}/{s['total']} items", 0, 27, size=11, font_path=font)

            # Progress bar
            bar_y = 40
            bar_w = 95
            oled.draw.line([(0, bar_y), (bar_w, bar_y)], fill=1)
            oled.draw.line([(0, bar_y + 7), (bar_w, bar_y + 7)], fill=1)
            oled.draw.line([(0, bar_y), (0, bar_y + 7)], fill=1)
            oled.draw.line([(bar_w, bar_y), (bar_w, bar_y + 7)], fill=1)
            fill = int(bar_w * min(s['pct'], 100) / 100)
            for y in range(bar_y + 1, bar_y + 7):
                oled.draw.line([(1, y), (max(1, fill), y)], fill=1)
            oled.draw_text(f"{s['pct']}%", bar_w + 4, bar_y - 1, size=9, font_path=font)

            # Days countdown
            oled.draw_text(f"{s['days_left']}d left", 40, 52, size=11, font_path=font)

        oled.display()
