"""Spirograph — rotating circles drawing evolving patterns."""
import math

SCREEN_W = 128
SCREEN_H = 64


class Spirograph:
    def __init__(self):
        self.t = 0.0
        self.R = 24.0  # Outer circle radius
        self.r = 9.0   # Inner circle radius
        self.d = 14.0  # Drawing point distance from inner center
        self.points = []
        self.max_points = 600
        self.morph_t = 0.0

    def step(self):
        self.t += 0.05
        self.morph_t += 0.001

        # Slowly morph parameters for evolving patterns
        self.r = 7.0 + math.sin(self.morph_t) * 4.0
        self.d = 12.0 + math.cos(self.morph_t * 0.7) * 5.0

        # Calculate new point (hypotrochoid equations)
        cx = SCREEN_W // 2
        cy = SCREEN_H // 2
        R, r, d = self.R, self.r, self.d

        x = cx + int((R - r) * math.cos(self.t) + d * math.cos((R - r) / r * self.t))
        y = cy + int((R - r) * math.sin(self.t) - d * math.sin((R - r) / r * self.t))

        # Clamp to screen
        x = max(0, min(SCREEN_W - 1, x))
        y = max(0, min(SCREEN_H - 1, y))

        self.points.append((x, y))
        if len(self.points) > self.max_points:
            self.points.pop(0)

    def render(self, oled):
        oled.clear()

        # Draw all points (older points could be faded but monochrome = all on)
        for x, y in self.points:
            oled.draw.point((x, y), fill=1)

        oled.display()

    def reset(self):
        self.__init__()

    def draw(self, oled):
        self.step()
        self.render(oled)
