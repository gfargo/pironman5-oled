"""Lorenz attractor — the classic butterfly-shaped strange attractor.

Numerically integrates the Lorenz system (sigma=10, rho=28, beta=8/3) with
simple Euler integration (dt=0.01) and projects the (x, z) plane onto the
128x64 display. The trail accumulates over time, revealing the
characteristic double-lobe "butterfly" shape after a few seconds.
"""

SCREEN_W = 128
SCREEN_H = 64

SIGMA = 10.0
RHO = 28.0
BETA = 8.0 / 3.0
DT = 0.01

# How many Euler steps to integrate per draw() call — keeps the butterfly
# shape emerging within a reasonable number of frames.
STEPS_PER_FRAME = 8

# Projection constants tuned so the attractor's natural (x, z) extents
# (x in ~[-20, 22], z in ~[0, 54]) fill the display with margin.
CENTER_X = SCREEN_W // 2
CENTER_Y = SCREEN_H // 2
SCALE_X = 2.5
SCALE_Z = 1.0
Z_OFFSET = 27.0

MAX_TRAIL = 1500


class LorenzAttractor:
    def __init__(self):
        self.reset()

    def _integrate_step(self):
        """Advance the Lorenz system by one Euler integration step."""
        x, y, z = self.x, self.y, self.z
        dx = SIGMA * (y - x)
        dy = x * (RHO - z) - y
        dz = x * y - BETA * z
        self.x = x + dx * DT
        self.y = y + dy * DT
        self.z = z + dz * DT

    def _project(self):
        """Project the (x, z) plane onto screen coordinates."""
        px = CENTER_X + int(self.x * SCALE_X)
        py = CENTER_Y - int((self.z - Z_OFFSET) * SCALE_Z)
        return px, py

    def step(self):
        for _ in range(STEPS_PER_FRAME):
            self._integrate_step()
            self.trail.append(self._project())

        if len(self.trail) > MAX_TRAIL:
            self.trail = self.trail[-MAX_TRAIL:]

    def render(self, oled):
        oled.clear()

        for px, py in self.trail:
            if 0 <= px < SCREEN_W and 0 <= py < SCREEN_H:
                oled.draw.point((px, py), fill=1)

        oled.display()

    def reset(self):
        # Slight perturbation off the origin — the origin is an unstable
        # fixed point of the system and would otherwise never diverge.
        self.x, self.y, self.z = 0.1, 0.0, 0.0
        self.trail = []

    def draw(self, oled):
        self.step()
        self.render(oled)
