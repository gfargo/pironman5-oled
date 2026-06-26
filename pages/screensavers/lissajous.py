"""Lissajous curves — parametric curves that morph slowly over time."""
import math

SCREEN_W = 128
SCREEN_H = 64


class Lissajous:
    def __init__(self):
        self.t = 0.0
        self.a_ratio = 3.0
        self.b_ratio = 2.0
        self.delta = 0.0
        self.trail = []
        self.max_trail = 300

    def step(self):
        self.t += 0.03
        # Slowly morph the curve parameters
        self.delta += 0.002
        self.a_ratio = 3.0 + math.sin(self.t * 0.1) * 1.5
        self.b_ratio = 2.0 + math.cos(self.t * 0.07) * 1.0

    def render(self, oled):
        oled.clear()

        # Draw the curve by sampling many points
        cx = SCREEN_W // 2
        cy = SCREEN_H // 2
        scale_x = 55
        scale_y = 25

        # Draw trail
        points = []
        for i in range(self.max_trail):
            phase = self.t - i * 0.02
            x = cx + int(math.sin(self.a_ratio * phase + self.delta) * scale_x)
            y = cy + int(math.sin(self.b_ratio * phase) * scale_y)
            if 0 <= x < SCREEN_W and 0 <= y < SCREEN_H:
                points.append((x, y))

        # Draw points (fade effect — draw every Nth point for older trail)
        for i, (x, y) in enumerate(points):
            # Older points are sparser
            if i < 100 or i % 2 == 0:
                oled.draw.point((x, y), fill=1)

        oled.display()

    def reset(self):
        self.__init__()

    def draw(self, oled):
        self.step()
        self.render(oled)
