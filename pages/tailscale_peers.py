"""Tailscale Peers — name, online/offline, and ping latency for each peer."""
import subprocess
import time
from pm_auto.libs.oled_page import OLEDPage
from pm_auto.libs.utils import get_font

from ._tailscale_util import parse_peers, parse_ping_latency, should_refetch

font = get_font('UbuntuSans-Regular.ttf')

CACHE_SECONDS = 30
PING_TIMEOUT = 2
MAX_PINGS = 5  # cap pings per refresh so we don't hammer the CLI


class PageTailscalePeers(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = []
        self._last_fetch = 0.0

    def _fetch_peers(self):
        try:
            result = subprocess.run(
                ['tailscale', 'status', '--json'],
                capture_output=True, text=True, timeout=5)
            peers = parse_peers(result.stdout)
        except Exception:
            return []

        online_peers = [p for p in peers if p['online']][:MAX_PINGS]
        for peer in online_peers:
            try:
                ping = subprocess.run(
                    ['tailscale', 'ping', '-c', '1', '--timeout', f'{PING_TIMEOUT}s', peer['name']],
                    capture_output=True, text=True, timeout=PING_TIMEOUT + 2)
                peer['latency'] = parse_ping_latency(ping.stdout)
            except Exception:
                peer['latency'] = None

        return peers

    def _get_peers(self):
        now = time.time()
        if not self._cache or should_refetch(self._last_fetch, now, CACHE_SECONDS):
            self._cache = self._fetch_peers()
            self._last_fetch = now
        return self._cache

    def main(self, oled, data, config):
        peers = self._get_peers()

        oled.clear()

        online = sum(1 for p in peers if p['online'])
        oled.draw_text('TAILSCALE', 0, 0, size=10, font_path=font)
        oled.draw_text(f"{online}/{len(peers)} up", 85, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        if not peers:
            oled.draw_text('not available', 0, 20, size=10, font_path=font)
            oled.display()
            return

        y = 15
        for peer in peers:
            if y > 60:
                break
            glyph = '*' if peer['online'] else 'x'
            if peer['online']:
                lat = f"{peer['latency']:.0f}ms" if peer['latency'] is not None else '--'
                oled.draw_text(f"{glyph} {peer['name']:<7} {lat}", 0, y, size=10, font_path=font)
            else:
                oled.draw_text(f"{glyph} {peer['name']:<7} offline", 0, y, size=10, font_path=font)
            y += 12

        oled.display()
