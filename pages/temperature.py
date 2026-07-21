"""Temperature Dashboard — CPU + NVMe temp with trend arrows."""
import subprocess
import time
from pm_auto.libs.oled_page import OLEDPage
from .pixel_font import get_pixel_font

font = get_pixel_font()


class PageTemperature(OLEDPage):
    def __init__(self):
        super().__init__()
        self._history_cpu = []
        self._history_nvme = []
        self._tick = 0
        self._max_history = 30

    def _get_temps(self):
        cpu_temp = 0
        nvme_temp = 0
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                cpu_temp = int(f.read()) // 1000
        except Exception:
            pass
        try:
            result = subprocess.run(
                ['smartctl', '-a', '/dev/nvme0n1'],
                capture_output=True, text=True, timeout=3)
            for line in result.stdout.split('\n'):
                if line.startswith('Temperature:'):
                    nvme_temp = int(line.split()[1])
                    break
        except Exception:
            pass
        return cpu_temp, nvme_temp

    def _trend(self, history):
        """Return trend arrow based on recent history."""
        if len(history) < 5:
            return "-"
        recent = history[-5:]
        diff = recent[-1] - recent[0]
        if diff > 2:
            return "^"  # rising
        elif diff < -2:
            return "v"  # falling
        return "="  # stable

    def main(self, oled, data, config):
        self._tick += 1

        # Sample every 5 ticks
        if self._tick % 5 == 0 or not self._history_cpu:
            cpu_temp, nvme_temp = self._get_temps()
            self._history_cpu.append(cpu_temp)
            self._history_nvme.append(nvme_temp)
            if len(self._history_cpu) > self._max_history:
                self._history_cpu.pop(0)
                self._history_nvme.pop(0)

        cpu_temp = self._history_cpu[-1] if self._history_cpu else 0
        nvme_temp = self._history_nvme[-1] if self._history_nvme else 0
        cpu_trend = self._trend(self._history_cpu)
        nvme_trend = self._trend(self._history_nvme)

        oled.clear()

        # Header
        oled.draw_text('TEMPS', 0, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        # CPU temp (large)
        oled.draw_text("CPU", 0, 16, size=10, font_path=font)
        oled.draw_text(f"{cpu_temp}C {cpu_trend}", 35, 14, size=16, font_path=font)

        # NVMe temp (large)
        oled.draw_text("NVMe", 0, 38, size=10, font_path=font)
        oled.draw_text(f"{nvme_temp}C {nvme_trend}", 35, 36, size=16, font_path=font)

        # Mini sparkline of CPU history (bottom)
        if len(self._history_cpu) > 2:
            min_t = max(min(self._history_cpu) - 5, 0)
            max_t = max(max(self._history_cpu) + 5, min_t + 10)
            spark_y = 56
            spark_h = 7
            for i, t in enumerate(self._history_cpu):
                x = int(i * (128 / self._max_history))
                y = spark_y + spark_h - int((t - min_t) * spark_h / (max_t - min_t))
                y = max(spark_y, min(spark_y + spark_h, y))
                oled.draw.point((x, y), fill=1)

        oled.display()
