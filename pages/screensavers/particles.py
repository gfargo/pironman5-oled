"""Screensaver: Bouncing Particles — dots ricocheting around the screen."""
import time
import random
from pm_auto.libs.utils import get_font

font = get_font('UbuntuSans-Regular.ttf')
SCREEN_W = 128
SCREEN_H = 64


class Particles:
    def __init__(self):
        self.particles = []
        self.last_time = 0

    def reset(self):
        self.particles = [
            {'x': random.uniform(10, 118), 'y': random.uniform(10, 54),
             'vx': random.uniform(-60, 60), 'vy': random.uniform(-60, 60),
             'char': random.choice(['o', '*', '+', '.'])}
            for _ in range(15)
        ]
        self.last_time = 0

    def draw(self, oled):
        now = time.time()
        dt = now - self.last_time if self.last_time > 0 else 0.05
        self.last_time = now
        dt = min(dt, 0.1)

        oled.clear()
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt

            if p['x'] <= 0 or p['x'] >= SCREEN_W - 4:
                p['vx'] *= -1
                p['x'] = max(0, min(SCREEN_W - 4, p['x']))
            if p['y'] <= 0 or p['y'] >= SCREEN_H - 6:
                p['vy'] *= -1
                p['y'] = max(0, min(SCREEN_H - 6, p['y']))

            oled.draw_text(p['char'], int(p['x']), int(p['y']), size=8, font_path=font)
        oled.display()
