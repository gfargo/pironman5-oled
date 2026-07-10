"""Screensaver: Bouncing Balls — gravity, elastic walls, and ball-ball collisions."""
import time
import random
import math
from dataclasses import dataclass

SCREEN_W = 128
SCREEN_H = 64

MIN_BALLS = 5
MAX_BALLS = 8
MIN_RADIUS = 2.0
MAX_RADIUS = 6.0
MAX_INITIAL_SPEED = 40.0
GRAVITY = 90.0  # px/s^2
BALL_RESTITUTION = 0.92  # ball-ball collisions lose a little energy so the system settles
MAX_SPAWN_ATTEMPTS = 200


@dataclass
class Ball:
    """A single bouncing ball."""
    x: float
    y: float
    vx: float
    vy: float
    radius: float


class BouncingBalls:
    def __init__(self):
        self.balls = []
        self.last_time = 0
        self.reset()

    def reset(self):
        self.balls = self._spawn_balls()
        self.last_time = 0

    def _spawn_balls(self) -> list:
        """Rejection-sample non-overlapping balls with random velocities."""
        count = random.randint(MIN_BALLS, MAX_BALLS)
        balls = []
        for _ in range(count):
            radius = random.uniform(MIN_RADIUS, MAX_RADIUS)
            placed = False
            for _attempt in range(MAX_SPAWN_ATTEMPTS):
                x = random.uniform(radius, SCREEN_W - radius)
                y = random.uniform(radius, SCREEN_H - radius)
                if all(
                    math.hypot(x - b.x, y - b.y) >= radius + b.radius
                    for b in balls
                ):
                    placed = True
                    break
            # If we can't find a non-overlapping spot after MAX_SPAWN_ATTEMPTS,
            # fall back to accepting the last sampled position rather than
            # looping forever.
            if not placed:
                x = random.uniform(radius, SCREEN_W - radius)
                y = random.uniform(radius, SCREEN_H - radius)

            vx = random.uniform(-MAX_INITIAL_SPEED, MAX_INITIAL_SPEED)
            vy = random.uniform(-MAX_INITIAL_SPEED, MAX_INITIAL_SPEED)
            balls.append(Ball(x=x, y=y, vx=vx, vy=vy, radius=radius))
        return balls

    def _apply_gravity(self, dt: float) -> None:
        for b in self.balls:
            b.vy += GRAVITY * dt

    def _integrate(self, dt: float) -> None:
        for b in self.balls:
            b.x += b.vx * dt
            b.y += b.vy * dt

    def _resolve_wall_collisions(self) -> None:
        """Perfectly elastic wall/floor bounces (restitution = 1.0)."""
        for b in self.balls:
            if b.x - b.radius < 0:
                b.x = b.radius
                b.vx = abs(b.vx)
            elif b.x + b.radius > SCREEN_W:
                b.x = SCREEN_W - b.radius
                b.vx = -abs(b.vx)

            if b.y - b.radius < 0:
                b.y = b.radius
                b.vy = abs(b.vy)
            elif b.y + b.radius > SCREEN_H:
                b.y = SCREEN_H - b.radius
                b.vy = -abs(b.vy)

    def _resolve_ball_collisions(self) -> None:
        """Simple circle-circle collision detection and elastic-with-restitution response."""
        n = len(self.balls)
        for i in range(n):
            for j in range(i + 1, n):
                a = self.balls[i]
                b = self.balls[j]

                dx = b.x - a.x
                dy = b.y - a.y
                dist = math.hypot(dx, dy)
                min_dist = a.radius + b.radius

                if dist >= min_dist:
                    continue

                # Guard against coincident centers to avoid division by zero.
                if dist < 1e-6:
                    dist = 1e-6
                    dx, dy = 1e-6, 0.0

                nx = dx / dist
                ny = dy / dist

                # Positional correction: push apart along the normal so they
                # no longer interpenetrate.
                overlap = min_dist - dist
                a.x -= nx * overlap / 2
                a.y -= ny * overlap / 2
                b.x += nx * overlap / 2
                b.y += ny * overlap / 2

                # Velocity response along the collision normal (equal mass).
                va_n = a.vx * nx + a.vy * ny
                vb_n = b.vx * nx + b.vy * ny
                closing = va_n - vb_n  # > 0 means approaching

                if closing > 0:
                    delta = (1 + BALL_RESTITUTION) / 2 * closing
                    a.vx -= delta * nx
                    a.vy -= delta * ny
                    b.vx += delta * nx
                    b.vy += delta * ny

    def _step(self, dt: float) -> None:
        self._apply_gravity(dt)
        self._integrate(dt)
        self._resolve_wall_collisions()
        self._resolve_ball_collisions()

    def draw(self, oled):
        now = time.time()
        dt = now - self.last_time if self.last_time > 0 else 0.05
        self.last_time = now
        dt = min(dt, 0.1)

        self._step(dt)

        oled.clear()
        for b in self.balls:
            oled.draw.ellipse(
                [b.x - b.radius, b.y - b.radius, b.x + b.radius, b.y + b.radius],
                fill=1,
            )
        oled.display()
