"""Uptime counter — large display of days:hours:minutes:seconds since boot."""
import time

SCREEN_W = 128
SCREEN_H = 64


class UptimeCounter:
    def __init__(self):
        self.boot_time = time.time() - self._get_uptime_seconds()

    def _get_uptime_seconds(self):
        try:
            with open('/proc/uptime', 'r') as f:
                return int(float(f.read().split()[0]))
        except Exception:
            return 0

    def step(self):
        pass  # Time advances naturally

    def render(self, oled):
        oled.clear()

        elapsed = int(time.time() - self.boot_time)
        days = elapsed // 86400
        hours = (elapsed % 86400) // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60

        # Large time display centered
        if days > 0:
            time_str = f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Draw "UPTIME" label small at top
        from pm_auto.libs.utils import get_font
        font = get_font('UbuntuSans-Regular.ttf')
        oled.draw_text("UPTIME", 40, 5, size=10, font_path=font)

        # Draw the time large and centered
        oled.draw_text(time_str, 8, 25, size=20, font_path=font)

        # Draw a subtle pulsing dot as "heartbeat" indicator
        if seconds % 2 == 0:
            oled.draw.point((SCREEN_W - 5, SCREEN_H - 5), fill=1)
            oled.draw.point((SCREEN_W - 4, SCREEN_H - 5), fill=1)
            oled.draw.point((SCREEN_W - 5, SCREEN_H - 4), fill=1)
            oled.draw.point((SCREEN_W - 4, SCREEN_H - 4), fill=1)

        oled.display()

    def reset(self):
        self.__init__()

    def draw(self, oled):
        self.step()
        self.render(oled)
