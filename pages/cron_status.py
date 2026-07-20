"""Cron Job Status — last cron job results with pass/fail indicators.

Data source: `journalctl -t CRON`. See cron_log.py for the pure parsing
logic (kept free of pm_auto/subprocess so it's unit-testable headless).
"""
import subprocess
from pm_auto.libs.oled_page import OLEDPage
from pm_auto.libs.utils import get_font
from .cron_log import parse_cron_log

font = get_font('UbuntuSans-Regular.ttf')

MAX_ENTRIES = 4


class PageCronStatus(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = None
        self._tick = 0

    def _get_cron_entries(self):
        self._tick += 1
        if self._cache is not None and self._tick % 60 != 0:
            return self._cache
        try:
            result = subprocess.run(
                ['journalctl', '-t', 'CRON', '-n', '200', '--no-pager'],
                capture_output=True, text=True, timeout=5)
            self._cache = parse_cron_log(result.stdout, limit=MAX_ENTRIES)
        except Exception:
            if self._cache is None:
                self._cache = []
        return self._cache

    def main(self, oled, data, config):
        entries = self._get_cron_entries()
        oled.clear()

        oled.draw_text('CRON', 0, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)
        if entries:
            passed = sum(1 for e in entries if e['ok'])
            oled.draw_text(f"{passed}/{len(entries)}", 104, 0, size=10, font_path=font)

        if not entries:
            oled.draw_text("No cron runs", 8, 26, size=11, font_path=font)
            oled.draw_text("found in log", 8, 40, size=11, font_path=font)
        else:
            for i, entry in enumerate(entries):
                y = 14 + i * 12
                indicator = "OK" if entry['ok'] else "FAIL"
                oled.draw_text(f"{entry['time']} {entry['command'][:11]}", 0, y, size=9, font_path=font)
                oled.draw_text(indicator, 104, y, size=9, font_path=font)

        oled.display()
