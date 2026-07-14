"""Raindrop ripples — random drops emit fading concentric rings."""
import math
import random
import time

SCREEN_W = 128
SCREEN_H = 64

MIN_RIPPLES = 3
MAX_RIPPLES = 5
SPAWN_MIN = 2.0
SPAWN_MAX = 3.0
RING_SPEED = 14.0  # px/sec
MAX_RADIUS = 46.0
RINGS_PER_DROP = 3
RING_GAP = 7.0


def _ring_point_count(radius):
    """Points to draw for a ring of the given radius — falls off as radius grows."""
    return max(4, int(80 / (1 + radius * 0.5)))


class RaindropRipples:
    def __init__(self):
        self.reset()

    def reset(self):
        self.ripples = []
        self.last_time = 0
        self.spawn_timer = random.uniform(SPAWN_MIN, SPAWN_MAX)
        for _ in range(MIN_RIPPLES):
            self._spawn(radius=random.uniform(0, MAX_RADIUS * 0.6))

    def _spawn(self, radius=0.0):
        self.ripples.append({
            'x': random.uniform(0, SCREEN_W - 1),
            'y': random.uniform(0, SCREEN_H - 1),
            'radius': radius,
        })

    def _step(self, dt):
        for ripple in self.ripples:
            ripple['radius'] += RING_SPEED * dt
        self.ripples = [r for r in self.ripples if r['radius'] < MAX_RADIUS]

        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and len(self.ripples) < MAX_RIPPLES:
            self._spawn()
            self.spawn_timer = random.uniform(SPAWN_MIN, SPAWN_MAX)

        while len(self.ripples) < MIN_RIPPLES:
            self._spawn()

    def _render(self, oled):
        oled.clear()
        for ripple in self.ripples:
            cx, cy = ripple['x'], ripple['y']
            for k in range(RINGS_PER_DROP):
                radius = ripple['radius'] - k * RING_GAP
                if radius <= 0:
                    continue
                num_points = _ring_point_count(radius)
                for i in range(num_points):
                    theta = (2 * math.pi * i) / num_points
                    x = int(cx + math.cos(theta) * radius)
                    y = int(cy + math.sin(theta) * radius)
                    if 0 <= x < SCREEN_W and 0 <= y < SCREEN_H:
                        oled.draw.point((x, y), fill=1)
        oled.display()

    def draw(self, oled):
        now = time.time()
        dt = now - self.last_time if self.last_time > 0 else 0.05
        self.last_time = now
        dt = min(dt, 0.1)

        self._step(dt)
        self._render(oled)
