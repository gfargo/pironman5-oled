"""Budget Burn Rate — Actual Budget monthly spend vs budget gauge."""
import json
import urllib.request
import time
import os
from datetime import datetime
from pm_auto.libs.oled_page import OLEDPage
from pm_auto.libs.utils import get_font

font = get_font('UbuntuSans-Regular.ttf')

# Actual Budget runs on compass:5016 (internal), HTTPS on :5006 (external)
ACTUAL_URL = os.environ.get('ACTUAL_URL', 'http://localhost:5016')
ACTUAL_PASSWORD = ''  # loaded from secrets file
ACTUAL_SYNC_ID = ''   # loaded from secrets file

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


class PageBudgetBurn(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = None
        self._tick = 0
        self._last_fetch = 0
        self._password = _load_secret('ACTUAL_PASSWORD')
        self._sync_id = _load_secret('ACTUAL_SYNC_ID')

    def _fetch_budget(self):
        now = time.time()
        # Refresh every 15 minutes
        if self._cache and (now - self._last_fetch) < 900:
            return self._cache

        data = {'spent': 0, 'budget': 0, 'pct': 0, 'days_left': 0}

        if not self._password:
            data['error'] = 'no credentials'
            self._cache = data
            return data

        # Calculate days remaining in month
        today = datetime.now()
        if today.month == 12:
            days_in_month = 31
        else:
            from calendar import monthrange
            days_in_month = monthrange(today.year, today.month)[1]
        data['days_left'] = days_in_month - today.day

        # Try to get budget summary from Actual's API
        # Note: Actual's API is complex (uses sync protocol). We'll try a simpler
        # approach: query the report endpoint if available, or show placeholder.
        try:
            # Actual uses a token-based auth after initial sync
            # For the OLED, we'll use a simplified approach
            url = f"{ACTUAL_URL}/api/v1/budgets"
            req = urllib.request.Request(url, headers={
                'Accept': 'application/json',
                'X-Actual-Password': self._password,
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read())
                # Parse budget data if available
                if isinstance(result, list) and result:
                    data['available'] = True
                    self._last_fetch = now
        except urllib.error.HTTPError as e:
            # 404 = API endpoint doesn't exist in this version
            data['error'] = f'HTTP {e.code}'
        except Exception as e:
            data['error'] = str(e)[:20]

        # Fallback: show days remaining and prompt to configure
        if 'error' in data or not data.get('available'):
            data['spent'] = 0
            data['budget'] = 0
            data['pct'] = 0

        self._cache = data
        self._last_fetch = now
        return data

    def main(self, oled, data_arg, config):
        b = self._fetch_budget()
        self._tick += 1
        oled.clear()

        # Header
        oled.draw_text('BUDGET', 0, 0, size=10, font_path=font)
        today = datetime.now()
        oled.draw_text(today.strftime("%b %Y"), 70, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        if b.get('error') == 'no credentials':
            oled.draw_text("Actual not", 18, 22, size=12, font_path=font)
            oled.draw_text("configured", 18, 38, size=12, font_path=font)
        elif b.get('error'):
            oled.draw_text("Actual Budget", 10, 18, size=11, font_path=font)
            oled.draw_text("connecting...", 14, 32, size=11, font_path=font)
            oled.draw_text(f"Days left: {b['days_left']}", 20, 50, size=10, font_path=font)
        else:
            # Spend gauge
            spent = b['spent']
            budget = b['budget']
            pct = b['pct']

            oled.draw_text(f"Spent: ${spent:,.0f}", 0, 15, size=11, font_path=font)
            oled.draw_text(f"Budget: ${budget:,.0f}", 0, 28, size=11, font_path=font)

            # Progress bar
            bar_y = 42
            bar_w = 100
            oled.draw.line([(0, bar_y), (bar_w, bar_y)], fill=1)
            oled.draw.line([(0, bar_y + 8), (bar_w, bar_y + 8)], fill=1)
            oled.draw.line([(0, bar_y), (0, bar_y + 8)], fill=1)
            oled.draw.line([(bar_w, bar_y), (bar_w, bar_y + 8)], fill=1)
            fill = int(bar_w * min(pct, 100) / 100)
            for y in range(bar_y + 1, bar_y + 8):
                oled.draw.line([(1, y), (fill, y)], fill=1)
            oled.draw_text(f"{pct}%", bar_w + 4, bar_y, size=9, font_path=font)

            # Days remaining
            oled.draw_text(f"{b['days_left']} days left", 30, 54, size=10, font_path=font)

        oled.display()
