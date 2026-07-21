"""Plane Stats — active issues, open items, workspace activity."""
import json
import urllib.request
from pm_auto.libs.oled_page import OLEDPage
from .pixel_font import get_pixel_font

font = get_pixel_font()

# Plane API on localhost (same host as Plane)
PLANE_API = "http://localhost:8080/api/v1"


class PagePlaneStats(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = None
        self._tick = 0

    def _fetch_stats(self):
        self._tick += 1
        # Only refresh every 60 ticks (~2 minutes at typical call rate)
        if self._cache and self._tick % 60 != 0:
            return self._cache

        stats = {'issues': '?', 'open': '?', 'projects': '?', 'error': None}

        try:
            # Try to get basic stats from the instance endpoint (no auth needed)
            req = urllib.request.Request(
                "http://localhost:8080/api/instances/",
                headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                # Instance endpoint gives basic info
                stats['instance'] = True
        except Exception as e:
            stats['error'] = str(e)[:30]

        # Try the monitor health endpoint for service status
        try:
            with urllib.request.urlopen("http://localhost:8080/api/instances/", timeout=3) as resp:
                stats['healthy'] = resp.status == 200
        except Exception:
            stats['healthy'] = False

        # Count running plane containers
        import subprocess
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=plane', '--format', '{{.Names}}'],
                capture_output=True, text=True, timeout=3)
            containers = [l for l in result.stdout.strip().split('\n') if l]
            stats['containers'] = len(containers)
        except Exception:
            stats['containers'] = 0

        self._cache = stats
        return self._cache

    def main(self, oled, data, config):
        stats = self._fetch_stats()
        oled.clear()

        # Header
        indicator = "OK" if stats.get('healthy') else "!"
        oled.draw_text('PLANE', 0, 0, size=10, font_path=font)
        oled.draw_text(indicator, 108, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        if stats.get('error') and not stats.get('healthy'):
            oled.draw_text("API unreachable", 0, 20, size=11, font_path=font)
            oled.draw_text(str(stats['error'])[:20], 0, 35, size=9, font_path=font)
        else:
            oled.draw_text(f"Containers: {stats.get('containers', '?')}", 0, 16, size=11, font_path=font)
            oled.draw_text(f"API: {'healthy' if stats.get('healthy') else 'down'}", 0, 30, size=11, font_path=font)
            oled.draw_text(f"https://:3443", 0, 44, size=10, font_path=font)

        oled.display()
