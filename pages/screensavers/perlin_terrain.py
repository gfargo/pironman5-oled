"""Perlin noise terrain — scrolling landscape like a side-view mountain range."""
import math
import random

SCREEN_W = 128
SCREEN_H = 64


def _noise_1d(x, seed=0):
    """Simple value noise (not true Perlin but visually similar at this scale)."""
    # Hash-based pseudo-random for deterministic noise at each x
    n = int(x) + seed * 131
    n = (n << 13) ^ n
    return 1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0


def _smooth_noise(x, seed=0):
    """Interpolated noise for smooth curves."""
    ix = int(math.floor(x))
    frac = x - ix
    # Smoothstep
    frac = frac * frac * (3 - 2 * frac)
    v0 = _noise_1d(ix, seed)
    v1 = _noise_1d(ix + 1, seed)
    return v0 + (v1 - v0) * frac


def _layered_noise(x, octaves=4, seed=0):
    """Multiple octaves of noise for natural terrain."""
    value = 0.0
    amp = 1.0
    freq = 1.0
    for i in range(octaves):
        value += _smooth_noise(x * freq, seed + i * 7) * amp
        amp *= 0.5
        freq *= 2.0
    return value


class PerlinTerrain:
    def __init__(self):
        self.scroll_x = 0.0
        self.seed = random.randint(0, 10000)

    def step(self):
        self.scroll_x += 0.3

    def render(self, oled):
        oled.clear()

        for x in range(SCREEN_W):
            # Sample noise at this x position (scrolling)
            nx = (x + self.scroll_x) * 0.02

            # Multiple terrain layers
            # Background mountains (tall, smooth)
            bg_height = _layered_noise(nx * 0.5, 3, self.seed) * 15 + 20
            # Foreground hills (shorter, rougher)
            fg_height = _layered_noise(nx, 4, self.seed + 100) * 12 + 40

            # Draw background (sparse dots)
            bg_y = int(SCREEN_H - bg_height)
            for y in range(bg_y, SCREEN_H):
                if (x + y) % 3 == 0:
                    oled.draw.point((x, y), fill=1)

            # Draw foreground (solid fill)
            fg_y = int(SCREEN_H - fg_height + 15)
            fg_y = max(bg_y + 5, fg_y)  # Keep in front
            for y in range(fg_y, SCREEN_H):
                oled.draw.point((x, y), fill=1)

            # Draw terrain outline
            oled.draw.point((x, fg_y), fill=1)

        oled.display()

    def reset(self):
        self.__init__()

    def draw(self, oled):
        self.step()
        self.render(oled)
