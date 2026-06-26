"""CPU/Memory Gauge — live bar graphs of CPU%, RAM%, and swap usage."""
import subprocess
from pm_auto.libs.oled_page import OLEDPage
from pm_auto.libs.utils import get_font

font = get_font('UbuntuSans-Regular.ttf')

SCREEN_W = 128
BAR_X = 32
BAR_W = 70
BAR_H = 10


class PageCpuMemory(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = None
        self._tick = 0

    def _get_stats(self):
        self._tick += 1
        if self._cache and self._tick % 3 != 0:
            return self._cache
        try:
            # CPU usage
            cpu = subprocess.run(
                ['sh', '-c', "top -bn1 | grep 'Cpu(s)' | awk '{print int($2+$4)}'"],
                capture_output=True, text=True, timeout=3)
            cpu_pct = int(cpu.stdout.strip()) if cpu.stdout.strip() else 0

            # Memory
            mem = subprocess.run(['free', '-b'], capture_output=True, text=True, timeout=3)
            lines = mem.stdout.strip().split('\n')
            mem_parts = lines[1].split()
            mem_total = int(mem_parts[1])
            mem_used = int(mem_parts[2])
            mem_pct = int(mem_used * 100 / mem_total) if mem_total > 0 else 0
            mem_gb = mem_used / (1024**3)
            mem_total_gb = mem_total / (1024**3)

            # Swap
            swap_pct = 0
            swap_used_mb = 0
            if len(lines) > 2:
                swap_parts = lines[2].split()
                swap_total = int(swap_parts[1])
                swap_used = int(swap_parts[2])
                swap_pct = int(swap_used * 100 / swap_total) if swap_total > 0 else 0
                swap_used_mb = swap_used / (1024**2)

            self._cache = {
                'cpu': cpu_pct,
                'mem_pct': mem_pct, 'mem_gb': mem_gb, 'mem_total_gb': mem_total_gb,
                'swap_pct': swap_pct, 'swap_mb': swap_used_mb,
            }
        except Exception:
            if not self._cache:
                self._cache = {'cpu': 0, 'mem_pct': 0, 'mem_gb': 0, 'mem_total_gb': 0, 'swap_pct': 0, 'swap_mb': 0}
        return self._cache

    def _draw_bar(self, oled, y, label, pct, detail):
        oled.draw_text(label, 0, y, size=10, font_path=font)
        # Bar outline
        oled.draw.line([(BAR_X, y + 1), (BAR_X + BAR_W, y + 1)], fill=1)
        oled.draw.line([(BAR_X, y + BAR_H), (BAR_X + BAR_W, y + BAR_H)], fill=1)
        oled.draw.line([(BAR_X, y + 1), (BAR_X, y + BAR_H)], fill=1)
        oled.draw.line([(BAR_X + BAR_W, y + 1), (BAR_X + BAR_W, y + BAR_H)], fill=1)
        # Fill
        fill_w = int(BAR_W * min(pct, 100) / 100)
        for fy in range(y + 2, y + BAR_H):
            oled.draw.line([(BAR_X + 1, fy), (BAR_X + fill_w, fy)], fill=1)
        # Percentage text
        oled.draw_text(detail, BAR_X + BAR_W + 2, y, size=8, font_path=font)

    def main(self, oled, data, config):
        stats = self._get_stats()
        oled.clear()

        # Header
        oled.draw_text('SYSTEM', 0, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        # CPU bar
        self._draw_bar(oled, 15, "CPU", stats['cpu'], f"{stats['cpu']}%")
        # Memory bar
        self._draw_bar(oled, 30, "MEM", stats['mem_pct'], f"{stats['mem_gb']:.1f}G")
        # Swap bar
        self._draw_bar(oled, 45, "SWP", stats['swap_pct'], f"{int(stats['swap_mb'])}M")

        oled.display()
