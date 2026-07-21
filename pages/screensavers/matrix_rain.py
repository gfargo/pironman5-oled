"""Screensaver: Matrix Rain — falling characters."""
import time
import random
from ..pixel_font import get_pixel_font

font = get_pixel_font()
SCREEN_W = 128
SCREEN_H = 64


class MatrixRain:
    def __init__(self):
        self.columns = []
        self.last_time = 0

    def reset(self):
        self.columns = [
            {'x': i * 8, 'y': random.randint(-30, SCREEN_H),
             'speed': random.uniform(40, 100),
             'chars': [chr(random.randint(33, 126)) for _ in range(8)]}
            for i in range(16)
        ]
        self.last_time = 0

    def draw(self, oled):
        now = time.time()
        dt = now - self.last_time if self.last_time > 0 else 0.05
        self.last_time = now
        dt = min(dt, 0.1)

        oled.clear()
        for col in self.columns:
            col['y'] += col['speed'] * dt

            for i in range(4):
                cy = int(col['y']) - i * 12
                if 0 <= cy < SCREEN_H:
                    char = col['chars'][(int(col['y'] / 12) + i) % len(col['chars'])]
                    sz = 10 if i == 0 else 8
                    oled.draw_text(char, col['x'], cy, size=sz, font_path=font)

            if col['y'] > SCREEN_H + 40:
                col['y'] = random.randint(-40, -10)
                col['speed'] = random.uniform(40, 100)
                col['chars'] = [chr(random.randint(33, 126)) for _ in range(8)]

        oled.display()
