"""Backup Status — fetches from watch hub API (no SSH needed)."""
import json
import time
import os
from pm_auto.libs.oled_page import OLEDPage
from pm_auto.libs.utils import get_font

font = get_font('UbuntuSans-Regular.ttf')

WATCH_HUB_URL = "http://watch:8090/api/stats"


class PageBackupStatus(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = None
        self._tick = 0

    def _get_backup_status(self):
        self._tick += 1
        if self._cache and self._tick % 120 != 0:
            return self._cache

        # Fetch from watch's hub API
        try:
            import urllib.request
            with urllib.request.urlopen(WATCH_HUB_URL, timeout=5) as resp:
                hub_data = json.loads(resp.read())
                bk = hub_data.get('backup')
                if bk and bk.get('date'):
                    self._cache = {
                        'date': bk.get('date', '??'),
                        'size': bk.get('size', '??'),
                        'age_hours': bk.get('age_hours', 99),
                        'healthy': bk.get('healthy', False),
                        'count': bk.get('count', 0),
                    }
                    return self._cache
        except Exception:
            pass

        if not self._cache:
            self._cache = {'date': 'unreachable', 'size': '-', 'age_hours': 99, 'healthy': False, 'count': 0}
        return self._cache

    def main(self, oled, data, config):
        status = self._get_backup_status()
        oled.clear()

        # Compact header
        indicator = "OK" if status['healthy'] else "!"
        oled.draw_text('BACKUP', 0, 0, size=10, font_path=font)
        oled.draw_text(indicator, 108, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        # Content
        oled.draw_text(f"Last: {status['date']}", 0, 14, size=10, font_path=font)
        oled.draw_text(f"Size: {status['size']}", 0, 26, size=10, font_path=font)

        age = status['age_hours']
        if age < 24:
            age_str = f"{age}h ago"
        elif age < 99:
            age_str = f"{age // 24}d ago"
        else:
            age_str = "??"
        oled.draw_text(f"Age:  {age_str}", 0, 38, size=10, font_path=font)
        if status['count'] > 0:
            oled.draw_text(f"Kept: {status['count']} dumps", 0, 50, size=10, font_path=font)

        oled.display()
