"""Pendulum wave — multiple pendulums with slightly different periods."""
import math
import time

SCREEN_W = 128
SCREEN_H = 64
NUM_PENDULUMS = 15


class PendulumWave:
    def __init__(self):
        self.t = 0.0
        # Each pendulum has a slightly different frequency
        # Creates the classic wave pattern that aligns periodically
        self.base_freq = 1.0
        self.freq_step = 0.06

    def step(self):
        self.t += 0.04

    def render(self, oled):
        oled.clear()

        # Draw the support bar
        oled.draw.line([(5, 5), (SCREEN_W - 5, 5)], fill=1)

        spacing = (SCREEN_W - 20) / (NUM_PENDULUMS - 1)

        for i in range(NUM_PENDULUMS):
            freq = self.base_freq + i * self.freq_step
            angle = math.sin(self.t * freq) * 0.8  # max swing ~45 degrees

            # Pivot point
            px = 10 + i * spacing
            py = 5

            # Pendulum length varies slightly for visual interest
            length = 35 + i * 1.2

            # Bob position
            bx = px + math.sin(angle) * length
            by = py + math.cos(angle) * length

            # Draw string
            oled.draw.line([(int(px), int(py)), (int(bx), int(by))], fill=1)
            # Draw bob (small circle approximation — just a cross)
            oled.draw.point((int(bx), int(by)), fill=1)
            oled.draw.point((int(bx) + 1, int(by)), fill=1)
            oled.draw.point((int(bx) - 1, int(by)), fill=1)
            oled.draw.point((int(bx), int(by) + 1), fill=1)
            oled.draw.point((int(bx), int(by) - 1), fill=1)

        oled.display()

    def reset(self):
        self.__init__()

    def draw(self, oled):
        self.step()
        self.render(oled)
