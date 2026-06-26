"""Screensaver: Starfield — stars flying outward from center."""
import time
import random
from pm_auto.libs.utils import get_font

font = get_font('UbuntuSans-Regular.ttf')
SCREEN_W = 128
SCREEN_H = 64


class Starfield:
    def __init__(self):
        self.stars = []
        self.last_time = 0

    def reset(self):
        self.stars = [
            {'x': 64 + random.uniform(-10, 10), 'y': 32 + random.uniform(-10, 10),
             'speed': random.uniform(20, 40)}
            for _ in range(25)
        ]
        self.last_time = 0

    def draw(self, oled):
        now = time.time()
        dt = now - self.last_time if self.last_time > 0 else 0.05
        self.last_time = now
        dt = min(dt, 0.1)

        oled.clear()
        for star in self.stars:
            star['x'] += (star['x'] - 64) * dt * 2.0
            star['y'] += (star['y'] - 32) * dt * 2.0
            star['speed'] += dt * 30

            if star['x'] < -5 or star['x'] > SCREEN_W + 5 or star['y'] < -5 or star['y'] > SCREEN_H + 5:
                star['x'] = 64 + random.uniform(-8, 8)
                star['y'] = 32 + random.uniform(-8, 8)
                star['speed'] = random.uniform(20, 40)

            ix, iy = int(star['x']), int(star['y'])
            if 0 <= ix < SCREEN_W and 0 <= iy < SCREEN_H:
                sz = 8 if star['speed'] < 60 else 10
                oled.draw_text(".", ix, iy, size=sz, font_path=font)
        oled.display()
