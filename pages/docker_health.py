"""Docker Health — container count + unhealthy list with pagination."""
import subprocess
import time
from pm_auto.libs.oled_page import OLEDPage
from pm_auto.libs.utils import get_font

font = get_font('UbuntuSans-Regular.ttf')


class PageDockerHealth(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = None
        self._tick = 0
        self._page = 0
        self._last_page_time = 0

    def _get_docker_status(self):
        self._tick += 1
        if self._cache and self._tick % 5 != 0:
            return self._cache
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'],
                capture_output=True, text=True, timeout=5)
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            running = len(lines)
            unhealthy = []
            for line in lines:
                parts = line.split('\t')
                if len(parts) == 2 and 'unhealthy' in parts[1].lower():
                    unhealthy.append(parts[0].replace('plane-', '').replace('-1', ''))
            result_all = subprocess.run(
                ['docker', 'ps', '-a', '--format', '{{.Names}}'],
                capture_output=True, text=True, timeout=5)
            total = len(result_all.stdout.strip().split('\n')) if result_all.stdout.strip() else 0
            self._cache = {'running': running, 'total': total, 'unhealthy': unhealthy}
        except Exception:
            if not self._cache:
                self._cache = {'running': 0, 'total': 0, 'unhealthy': ['error']}
        return self._cache

    def main(self, oled, data, config):
        status = self._get_docker_status()
        running = status['running']
        total = status['total']
        unhealthy = status['unhealthy']

        oled.clear()

        # Compact header (12px)
        oled.draw_text('DOCKER', 0, 0, size=10, font_path=font)
        oled.draw_text(f"{running}/{total}", 90, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        if unhealthy:
            # Paginate: 4 items per view
            per_page = 4
            pages = (len(unhealthy) + per_page - 1) // per_page
            now = time.time()
            if now - self._last_page_time > 3 and pages > 1:
                self._page = (self._page + 1) % pages
                self._last_page_time = now

            start = self._page * per_page
            for i, name in enumerate(unhealthy[start:start + per_page]):
                y = 15 + (i * 12)
                oled.draw_text(f"! {name[:18]}", 0, y, size=10, font_path=font)
        else:
            oled.draw_text("ALL HEALTHY", 24, 30, size=12, font_path=font)

        oled.display()
