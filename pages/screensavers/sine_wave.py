"""Screensaver: Sine Waves — flowing oscillating lines."""
import time
import math
from pm_auto.libs.utils import get_font

font = get_font('UbuntuSans-Regular.ttf')
SCREEN_W = 128
SCREEN_H = 64


class SineWave:
    def __init__(self):
        self.phase = 0.0
        self.last_time = 0

    def reset(self):
        self.phase = 0.0
        self.last_time = 0

    def draw(self, oled):
        now = time.time()
        dt = now - self.last_time if self.last_time > 0 else 0.05
        self.last_time = now
        dt = min(dt, 0.1)
        self.phase += dt * 3

        oled.clear()
        for x in range(0, SCREEN_W, 3):
            y1 = 32 + int(22 * math.sin((x / 18.0) + self.phase))
            y2 = 32 + int(14 * math.sin((x / 11.0) + self.phase * 1.7 + 1.5))
            y3 = 32 + int(8 * math.sin((x / 7.0) + self.phase * 2.3 + 3.0))
            for y in [y1, y2, y3]:
                if 0 <= y < SCREEN_H:
                    oled.draw_text(".", x, y, size=8, font_path=font)
        oled.display()
