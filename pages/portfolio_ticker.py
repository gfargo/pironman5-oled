"""Portfolio Ticker — Ghostfolio net worth + daily % change."""
import json
import urllib.request
import time
import os
from pm_auto.libs.oled_page import OLEDPage
from pm_auto.libs.utils import get_font

font = get_font('UbuntuSans-Regular.ttf')

# Ghostfolio runs on compass:3334 (internal), HTTPS on :3333 (external)
GHOSTFOLIO_URL = os.environ.get('GHOSTFOLIO_URL', 'http://localhost:3334')
GHOSTFOLIO_TOKEN = os.environ.get('GHOSTFOLIO_TOKEN', '')

SECRETS_FILE = '/opt/pironman5/oled-secrets.env'


def _load_secret(key):
    """Load a secret from the env file if not already in environment."""
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


class PagePortfolioTicker(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = None
        self._tick = 0
        self._last_fetch = 0
        self._token = _load_secret('GHOSTFOLIO_TOKEN')

    def _fetch_portfolio(self):
        now = time.time()
        # Refresh every 10 minutes
        if self._cache and (now - self._last_fetch) < 600:
            return self._cache

        data = {'value': '?', 'change_pct': 0, 'change_abs': 0, 'currency': 'USD'}

        if not self._token:
            data['error'] = 'no token'
            self._cache = data
            return data

        try:
            url = f"{GHOSTFOLIO_URL}/api/v1/portfolio/performance?range=1d"
            req = urllib.request.Request(url, headers={
                'Authorization': f'Bearer {self._token}',
                'Accept': 'application/json'
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                perf = result.get('performance', result)
                data['value'] = perf.get('currentNetWorth', perf.get('currentValue', '?'))
                data['change_pct'] = perf.get('netPerformancePercentage', 0)
                data['change_abs'] = perf.get('netPerformance', 0)
                data['currency'] = perf.get('currency', 'USD')
                self._last_fetch = now
        except Exception as e:
            data['error'] = str(e)[:25]

        self._cache = data
        return data

    def main(self, oled, data_arg, config):
        p = self._fetch_portfolio()
        self._tick += 1
        oled.clear()

        # Header
        oled.draw_text('PORTFOLIO', 0, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        if p.get('error') == 'no token':
            oled.draw_text("Token not", 20, 22, size=12, font_path=font)
            oled.draw_text("configured", 18, 38, size=12, font_path=font)
        elif p.get('error'):
            oled.draw_text("Ghostfolio", 18, 22, size=12, font_path=font)
            oled.draw_text("unreachable", 16, 38, size=11, font_path=font)
        else:
            # Net worth (large)
            value = p['value']
            if isinstance(value, (int, float)):
                value_str = f"${value:,.0f}"
            else:
                value_str = str(value)
            oled.draw_text(value_str, 5, 15, size=18, font_path=font)

            # Daily change
            change_pct = p['change_pct']
            change_abs = p['change_abs']
            if isinstance(change_pct, (int, float)):
                arrow = "^" if change_pct >= 0 else "v"
                sign = "+" if change_pct >= 0 else ""
                pct_str = f"{arrow} {sign}{change_pct:.2f}%"
                abs_str = f"({sign}${abs(change_abs):,.0f})" if isinstance(change_abs, (int, float)) else ""
            else:
                pct_str = "? %"
                abs_str = ""

            oled.draw_text(pct_str, 5, 40, size=14, font_path=font)
            oled.draw_text(abs_str, 5, 55, size=9, font_path=font)

        oled.display()
