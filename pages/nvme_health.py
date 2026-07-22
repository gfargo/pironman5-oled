"""NVMe Health — drive temp, wear, written data via smartctl."""
import subprocess
import re
from pm_auto.libs.oled_page import OLEDPage
from .pixel_font import get_pixel_font

font = get_pixel_font()


class PageNVMeHealth(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = None
        self._tick = 0

    def _get_nvme_info(self):
        self._tick += 1
        if self._cache and self._tick % 120 != 0:
            return self._cache
        try:
            result = subprocess.run(['smartctl', '-a', '/dev/nvme0'],
                                    capture_output=True, text=True, timeout=10)
            output = result.stdout
            temp_match = re.search(r'Temperature:\s+(\d+)\s+Celsius', output)
            temp = int(temp_match.group(1)) if temp_match else 0
            wear_match = re.search(r'Percentage Used:\s+(\d+)%', output)
            wear = int(wear_match.group(1)) if wear_match else 0
            written_match = re.search(r'Data Units Written:.*?\[(.+?)\]', output)
            written = written_match.group(1).strip() if written_match else '??'
            hours_match = re.search(r'Power On Hours:\s+([\d,]+)', output)
            hours = int(hours_match.group(1).replace(',', '')) if hours_match else 0
            self._cache = {'temp': temp, 'wear': wear, 'written': written, 'hours': hours,
                           'healthy': wear < 80 and temp < 70}
        except Exception:
            try:
                import glob
                temp_files = glob.glob('/sys/class/nvme/nvme0/hwmon*/temp1_input')
                if temp_files:
                    with open(temp_files[0]) as f:
                        temp = int(f.read()) // 1000
                    self._cache = {'temp': temp, 'wear': 0, 'written': '??', 'hours': 0, 'healthy': True}
            except Exception:
                if not self._cache:
                    self._cache = {'temp': 0, 'wear': 0, 'written': '??', 'hours': 0, 'healthy': True}
        return self._cache

    def main(self, oled, data, config):
        info = self._get_nvme_info()
        oled.clear()

        # Compact header
        status = "OK" if info['healthy'] else "WARN"
        oled.draw_text('NVMe', 0, 0, size=10, font_path=font)
        oled.draw_text(status, 108, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        # Content
        oled.draw_text(f"Temp:    {info['temp']}C", 0, 14, size=10, font_path=font)
        oled.draw_text(f"Wear:    {info['wear']}%", 0, 26, size=10, font_path=font)
        oled.draw_text(f"Written: {info['written']}", 0, 38, size=10, font_path=font)
        oled.draw_text(f"Hours:   {info['hours']:,}", 0, 50, size=10, font_path=font)

        oled.display()
