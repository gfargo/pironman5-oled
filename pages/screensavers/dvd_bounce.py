"""Screensaver: Bouncing DVD Logo."""
import time
from ..pixel_font import get_pixel_font

font = get_pixel_font()

LOGO_W = 26
LOGO_H = 12
SCREEN_W = 128
SCREEN_H = 64


class DVDBounce:
    def __init__(self):
        self.x = 10.0
        self.y = 20.0
        self.vx = 1.5
        self.vy = 1.0
        self.hits = 0
        self.last_time = 0

    def reset(self):
        import random
        self.x = random.uniform(10, 90)
        self.y = random.uniform(10, 40)
        self.vx = 1.5 * (1 if random.random() > 0.5 else -1)
        self.vy = 1.0 * (1 if random.random() > 0.5 else -1)
        self.hits = 0
        self.last_time = 0

    def draw(self, oled):
        now = time.time()
        dt = now - self.last_time if self.last_time > 0 else 0.05
        self.last_time = now
        dt = min(dt, 0.1)

        speed = 60
        self.x += self.vx * speed * dt
        self.y += self.vy * speed * dt

        hit = False
        if self.x <= 0:
            self.x = 0; self.vx = abs(self.vx); hit = True
        elif self.x >= SCREEN_W - LOGO_W:
            self.x = SCREEN_W - LOGO_W; self.vx = -abs(self.vx); hit = True
        if self.y <= 0:
            self.y = 0; self.vy = abs(self.vy); hit = True
        elif self.y >= SCREEN_H - LOGO_H:
            self.y = SCREEN_H - LOGO_H; self.vy = -abs(self.vy); hit = True

        if hit:
            self.hits += 1
            self.vx += (hash(str(now)) % 5 - 2) * 0.1
            self.vy += (hash(str(now * 2)) % 5 - 2) * 0.1
            self.vx = max(-2.0, min(2.0, self.vx))
            self.vy = max(-1.5, min(1.5, self.vy))

        oled.clear()
        oled.draw_text("DVD", int(self.x), int(self.y), size=14, font_path=font)
        if self.hits > 0:
            oled.draw_text(f"{self.hits}", 116, 56, size=8, font_path=font)
        oled.display()
