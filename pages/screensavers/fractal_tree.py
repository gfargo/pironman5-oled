"""Fractal tree — recursive branches that sway in the wind."""
import math
import time
import random

SCREEN_W = 128
SCREEN_H = 64


class FractalTree:
    def __init__(self):
        self.wind_offset = 0.0
        self.wind_speed = random.uniform(0.3, 0.8)

    def _draw_branch(self, oled, x, y, angle, length, depth):
        if depth <= 0 or length < 2:
            return

        # Wind effect increases with height
        wind = math.sin(self.wind_offset + y * 0.05) * 0.15 * (1 - y / SCREEN_H)

        end_x = x + math.cos(angle + wind) * length
        end_y = y - math.sin(angle + wind) * length

        oled.draw.line([(int(x), int(y)), (int(end_x), int(end_y))], fill=1)

        # Branch into two
        new_length = length * random.uniform(0.65, 0.75)
        spread = random.uniform(0.3, 0.5)
        self._draw_branch(oled, end_x, end_y, angle + spread, new_length, depth - 1)
        self._draw_branch(oled, end_x, end_y, angle - spread, new_length, depth - 1)

    def step(self):
        self.wind_offset += self.wind_speed * 0.05

    def render(self, oled):
        oled.clear()
        # Seed the random state for consistent tree shape (wind varies it)
        random.seed(42)
        self._draw_branch(oled, SCREEN_W // 2, SCREEN_H - 1, math.pi / 2, 18, 8)
        random.seed()  # Restore random state
        oled.display()

    def reset(self):
        self.__init__()

    def draw(self, oled):
        self.step()
        self.render(oled)
