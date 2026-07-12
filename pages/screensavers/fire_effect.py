"""Demoscene fire — classic heat propagation from bottom to top with cooling.

Each pixel's heat is the average of the three neighbors directly below it,
minus a random cooling factor. Heat intensity is mapped to a dithering
pattern (solid -> checkerboard -> sparse dots -> empty) so the effect reads
on a monochrome OLED.
"""
import random

SCREEN_W = 128
SCREEN_H = 64

BLOCK = 2  # each heat cell renders as a BLOCK x BLOCK pixel block
FIRE_COLS = SCREEN_W // BLOCK
FIRE_ROWS = SCREEN_H // BLOCK

HEAT_MAX = 16
COOLING_MIN = 0.5
COOLING_MAX = 3.0
SOURCE_MIN = 12
SOURCE_MAX = HEAT_MAX

# Dither offsets within a BLOCK x BLOCK cell, keyed by heat level (0 = coldest).
DITHER_OFFSETS = {
    0: [],
    1: [(0, 0)],
    2: [(0, 0), (1, 1)],
    3: [(0, 0), (1, 0), (0, 1), (1, 1)],
}


def _heat_level(value, heat_max):
    """Map a heat value to a dither level (0=empty .. 3=solid) by quartile."""
    if heat_max <= 0:
        return 0
    ratio = value / heat_max
    if ratio >= 0.75:
        return 3
    if ratio >= 0.5:
        return 2
    if ratio >= 0.25:
        return 1
    return 0


def _propagate(heat, cooling_min=COOLING_MIN, cooling_max=COOLING_MAX, heat_max=HEAT_MAX, rng=random):
    """Propagate heat upward: each cell = avg(3 neighbors below) - random cooling.

    The bottom row is left untouched (it's the fire source, refreshed separately).
    Reads only from the previous frame's `heat`, so results don't depend on
    iteration order.
    """
    rows = len(heat)
    cols = len(heat[0]) if rows else 0
    new_heat = [row[:] for row in heat]

    for y in range(rows - 1):
        below = heat[y + 1]
        for x in range(cols):
            left = below[x - 1] if x > 0 else below[x]
            right = below[x + 1] if x < cols - 1 else below[x]
            avg = (left + below[x] + right) / 3.0
            cooling = rng.uniform(cooling_min, cooling_max)
            new_heat[y][x] = max(0.0, min(heat_max, avg - cooling))

    return new_heat


class FireEffect:
    def __init__(self):
        self.reset()

    def reset(self):
        self.heat = [[0.0] * FIRE_COLS for _ in range(FIRE_ROWS)]

    def _ignite_source_row(self):
        """Refresh the bottom row with high, flickering heat values."""
        bottom = self.heat[FIRE_ROWS - 1]
        for x in range(FIRE_COLS):
            bottom[x] = random.randint(SOURCE_MIN, SOURCE_MAX)

    def _render_frame(self, oled):
        oled.clear()
        for y in range(FIRE_ROWS):
            row = self.heat[y]
            py = y * BLOCK
            for x in range(FIRE_COLS):
                level = _heat_level(row[x], HEAT_MAX)
                if level == 0:
                    continue
                px = x * BLOCK
                for dx, dy in DITHER_OFFSETS[level]:
                    oled.draw.point((px + dx, py + dy), fill=1)
        oled.display()

    def draw(self, oled):
        self._ignite_source_row()
        self.heat = _propagate(self.heat)
        self._render_frame(oled)
