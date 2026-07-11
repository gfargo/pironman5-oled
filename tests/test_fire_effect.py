"""Tests for the fire_effect screensaver's heat-propagation logic."""
import random
import sys

sys.path.insert(0, sys.path[0].replace('/tests', '/pages/screensavers'))
from fire_effect import (
    FireEffect,
    _heat_level,
    _propagate,
    FIRE_COLS,
    FIRE_ROWS,
    HEAT_MAX,
    SOURCE_MIN,
    SOURCE_MAX,
    DITHER_OFFSETS,
)


def test_heat_level_thresholds():
    assert _heat_level(0, HEAT_MAX) == 0
    assert _heat_level(HEAT_MAX * 0.24, HEAT_MAX) == 0
    assert _heat_level(HEAT_MAX * 0.25, HEAT_MAX) == 1
    assert _heat_level(HEAT_MAX * 0.49, HEAT_MAX) == 1
    assert _heat_level(HEAT_MAX * 0.5, HEAT_MAX) == 2
    assert _heat_level(HEAT_MAX * 0.74, HEAT_MAX) == 2
    assert _heat_level(HEAT_MAX * 0.75, HEAT_MAX) == 3
    assert _heat_level(HEAT_MAX, HEAT_MAX) == 3


def test_heat_level_zero_max():
    assert _heat_level(5, 0) == 0


def test_dither_offsets_monotonically_denser():
    assert DITHER_OFFSETS[0] == []
    assert len(DITHER_OFFSETS[1]) < len(DITHER_OFFSETS[2]) < len(DITHER_OFFSETS[3])
    assert len(DITHER_OFFSETS[3]) == 4  # fully solid block


def test_propagate_averages_neighbors_below_with_no_cooling():
    """With cooling forced to 0, each new cell is exactly the average of the
    three cells below it (no cooling applied)."""
    heat = [[0.0] * 4 for _ in range(3)]
    heat[2] = [4.0, 8.0, 12.0, 16.0]  # source row

    new_heat = _propagate(heat, cooling_min=0.0, cooling_max=0.0, heat_max=HEAT_MAX)

    # row 1 pulls from row 2 with wraparound neighbors
    expected_row1 = [
        (heat[2][3] + heat[2][0] + heat[2][1]) / 3.0,
        (heat[2][0] + heat[2][1] + heat[2][2]) / 3.0,
        (heat[2][1] + heat[2][2] + heat[2][3]) / 3.0,
        (heat[2][2] + heat[2][3] + heat[2][0]) / 3.0,
    ]
    for actual, expected in zip(new_heat[1], expected_row1):
        assert abs(actual - expected) < 1e-9

    # source row (last row) is left untouched by propagate
    assert new_heat[2] == heat[2]


def test_propagate_clamps_to_heat_max_and_zero():
    heat = [[HEAT_MAX] * 3, [HEAT_MAX] * 3]
    # Cooling range guaranteed negative-enough to floor at 0
    new_heat = _propagate(heat, cooling_min=HEAT_MAX * 10, cooling_max=HEAT_MAX * 10, heat_max=HEAT_MAX)
    assert new_heat[0] == [0.0, 0.0, 0.0]

    # Cooling forced to 0 with an over-max source clamps at heat_max
    heat2 = [[HEAT_MAX * 2] * 3, [HEAT_MAX * 2] * 3]
    new_heat2 = _propagate(heat2, cooling_min=0.0, cooling_max=0.0, heat_max=HEAT_MAX)
    assert new_heat2[0] == [HEAT_MAX, HEAT_MAX, HEAT_MAX]


def test_propagate_is_deterministic_given_seeded_rng():
    heat = [[HEAT_MAX] * FIRE_COLS for _ in range(FIRE_ROWS)]
    rng_a = random.Random(1234)
    rng_b = random.Random(1234)
    result_a = _propagate(heat, rng=rng_a)
    result_b = _propagate(heat, rng=rng_b)
    assert result_a == result_b


def test_propagate_does_not_mutate_input():
    heat = [[3.0, 5.0], [7.0, 9.0]]
    original = [row[:] for row in heat]
    _propagate(heat, cooling_min=0.0, cooling_max=0.0)
    assert heat == original


def test_fire_effect_ignite_source_row_within_bounds():
    fire = FireEffect()
    fire._ignite_source_row()
    bottom = fire.heat[FIRE_ROWS - 1]
    assert len(bottom) == FIRE_COLS
    assert all(SOURCE_MIN <= v <= SOURCE_MAX for v in bottom)


def test_fire_effect_reset_starts_cold():
    fire = FireEffect()
    fire.heat[0][0] = 99.0
    fire.reset()
    assert all(v == 0.0 for row in fire.heat for v in row)
    assert len(fire.heat) == FIRE_ROWS
    assert len(fire.heat[0]) == FIRE_COLS


class _MockDraw:
    def __init__(self):
        self.points = []

    def point(self, coord, fill=1):
        self.points.append(coord)


class _MockOLED:
    def __init__(self):
        self.draw = _MockDraw()
        self.cleared = False
        self.displayed = False

    def clear(self):
        self.cleared = True
        self.draw.points = []

    def display(self):
        self.displayed = True


def test_fire_effect_draw_smoke():
    fire = FireEffect()
    oled = _MockOLED()
    for _ in range(10):
        fire.draw(oled)
    assert oled.cleared
    assert oled.displayed
    # The fire source keeps injecting heat, so something should be lit.
    assert len(oled.draw.points) > 0
