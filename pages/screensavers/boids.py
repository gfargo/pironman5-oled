"""Screensaver: Boids flocking simulation.

20-28 triangular agents following the three classic rules:
  - Separation  : avoid crowding nearby neighbours
  - Alignment   : steer toward average heading of neighbours
  - Cohesion    : steer toward centre of mass of neighbours

Agents wrap at all four screen edges.
No font import — drawn as polygons/lines so importable in CI.
"""
import math
import random
import time

SCREEN_W = 128
SCREEN_H = 64

NUM_BOIDS = 24

# Tunable physics constants
NEIGHBOR_RADIUS = 20.0    # distance within which a boid is considered a neighbour
SEPARATION_RADIUS = 8.0   # distance within which separation kicks in harder
MAX_SPEED = 50.0          # px/s
MIN_SPEED = 15.0          # px/s — avoid motionless boids

# Rule weights
SEP_W = 1.4               # separation
ALI_W = 0.9               # alignment
COH_W = 0.7               # cohesion

# Triangle geometry
TRI_NOSE = 5              # px from centre to nose
TRI_TAIL = 3              # px from centre to tail vertices (perpendicular)
TRI_BACK = 3              # px behind centre to tail-base midpoint


def _make_boid(x, y, vx, vy):
    return {'x': float(x), 'y': float(y), 'vx': float(vx), 'vy': float(vy)}


class Boids:
    def __init__(self):
        self.boids = []
        self.last_time = 0.0

    def reset(self):
        self.boids = []
        for _ in range(NUM_BOIDS):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(MIN_SPEED, MAX_SPEED * 0.6)
            self.boids.append(_make_boid(
                x=random.uniform(0, SCREEN_W),
                y=random.uniform(0, SCREEN_H),
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
            ))
        self.last_time = 0.0

    # ------------------------------------------------------------------
    # Pure logic — testable without a display
    # ------------------------------------------------------------------

    def _step(self, dt):
        """Advance simulation by dt seconds (pure — no oled reference)."""
        new_boids = []
        for b in self.boids:
            sep_x = sep_y = 0.0
            ali_vx = ali_vy = 0.0
            coh_x = coh_y = 0.0
            n_ali = n_coh = n_sep = 0

            for other in self.boids:
                if other is b:
                    continue
                dx = other['x'] - b['x']
                dy = other['y'] - b['y']
                # Account for wrapping: use shortest path
                if dx > SCREEN_W / 2:
                    dx -= SCREEN_W
                elif dx < -SCREEN_W / 2:
                    dx += SCREEN_W
                if dy > SCREEN_H / 2:
                    dy -= SCREEN_H
                elif dy < -SCREEN_H / 2:
                    dy += SCREEN_H

                dist = math.sqrt(dx * dx + dy * dy)

                if dist < NEIGHBOR_RADIUS:
                    # Alignment
                    ali_vx += other['vx']
                    ali_vy += other['vy']
                    n_ali += 1

                    # Cohesion
                    coh_x += dx
                    coh_y += dy
                    n_coh += 1

                if dist < SEPARATION_RADIUS and dist > 0:
                    # Steer *away* — vector from other to self, scaled by proximity
                    sep_x -= dx / dist
                    sep_y -= dy / dist
                    n_sep += 1

            # Compute steering deltas
            steer_x = steer_y = 0.0

            # Separation — averaged over neighbours, then weighted
            if n_sep > 0:
                steer_x += (sep_x / n_sep) * SEP_W
                steer_y += (sep_y / n_sep) * SEP_W

            # Alignment — steer toward average heading
            if n_ali > 0:
                avg_vx = ali_vx / n_ali
                avg_vy = ali_vy / n_ali
                steer_x += (avg_vx - b['vx']) * ALI_W
                steer_y += (avg_vy - b['vy']) * ALI_W

            # Cohesion — steer toward centre of mass
            if n_coh > 0:
                steer_x += (coh_x / n_coh) * COH_W
                steer_y += (coh_y / n_coh) * COH_W

            # Apply steering (dt applied once here for all rules)
            nvx = b['vx'] + steer_x * dt
            nvy = b['vy'] + steer_y * dt

            # Clamp speed to [MIN_SPEED, MAX_SPEED]
            speed = math.sqrt(nvx * nvx + nvy * nvy)
            if speed > MAX_SPEED:
                nvx = nvx / speed * MAX_SPEED
                nvy = nvy / speed * MAX_SPEED
            elif speed < MIN_SPEED and speed > 0:
                nvx = nvx / speed * MIN_SPEED
                nvy = nvy / speed * MIN_SPEED
            elif speed == 0:
                # Frozen boid — give it a random kick
                angle = random.uniform(0, 2 * math.pi)
                nvx = math.cos(angle) * MIN_SPEED
                nvy = math.sin(angle) * MIN_SPEED

            # Integrate position and wrap
            nx = (b['x'] + nvx * dt) % SCREEN_W
            ny = (b['y'] + nvy * dt) % SCREEN_H

            new_boids.append(_make_boid(nx, ny, nvx, nvy))

        self.boids = new_boids

    def _triangle_points(self, boid):
        """Return 3 (x, y) vertices for a triangle oriented in the boid's heading.

        Nose at heading direction (TRI_NOSE px from centre), two tail vertices
        perpendicular at ±90° (TRI_TAIL px) offset TRI_BACK px behind centre.
        Pure / testable.
        """
        heading = math.atan2(boid['vy'], boid['vx'])
        cx, cy = boid['x'], boid['y']

        # Nose vertex
        nx = cx + math.cos(heading) * TRI_NOSE
        ny = cy + math.sin(heading) * TRI_NOSE

        # Tail base centre (behind nose)
        perp = heading + math.pi
        base_x = cx + math.cos(perp) * TRI_BACK
        base_y = cy + math.sin(perp) * TRI_BACK

        # Two tail vertices (perpendicular to heading)
        left = heading + math.pi / 2
        right = heading - math.pi / 2
        lx = base_x + math.cos(left) * TRI_TAIL
        ly = base_y + math.sin(left) * TRI_TAIL
        rx = base_x + math.cos(right) * TRI_TAIL
        ry = base_y + math.sin(right) * TRI_TAIL

        return (
            (int(round(nx)), int(round(ny))),
            (int(round(lx)), int(round(ly))),
            (int(round(rx)), int(round(ry))),
        )

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self, oled):
        """Draw all boids onto the OLED."""
        oled.clear()
        for b in self.boids:
            pts = self._triangle_points(b)
            # Draw the three edges of the triangle
            oled.draw.line([pts[0], pts[1]], fill=1)
            oled.draw.line([pts[1], pts[2]], fill=1)
            oled.draw.line([pts[2], pts[0]], fill=1)
        oled.display()

    def draw(self, oled):
        """Called every frame by the orchestrator."""
        now = time.time()
        dt = now - self.last_time if self.last_time > 0 else 0.05
        self.last_time = now
        dt = min(dt, 0.1)

        self._step(dt)
        self._render(oled)
