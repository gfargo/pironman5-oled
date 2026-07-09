"""Unit tests for morphing_clock.py — pure-logic layer, no hardware needed."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pages', 'screensavers'))

from morphing_clock import (
    SEGMENTS, DIGIT_COLS, DIGIT_Y, DIGIT_W, DIGIT_H,
    DigitMorph, _interp_segment, _segment_lines, MorphingClock,
)


def test_glyph_table():
    assert len(SEGMENTS) == 10, "Must have one mask per digit 0-9"

    # Digit 8: all 7 segments on
    assert all(SEGMENTS[8]), "Digit 8 must have all segments on"

    # Digit 1: only b (index 1) and c (index 2) on
    assert SEGMENTS[1] == (False, True, True, False, False, False, False)

    # Digit 0: 6 segments on (all except g at index 6)
    assert sum(SEGMENTS[0]) == 6
    assert SEGMENTS[0][6] is False


def test_interp_segment_bounds():
    ts = [0.0, 0.25, 0.5, 0.75, 1.0]

    for t in ts:
        # Both off: always 0
        assert _interp_segment(False, False, t) == 0.0
        # Both on: always 1
        assert _interp_segment(True, True, t) == 1.0
        # Result always in [0, 1]
        for a, b in [(False, True), (True, False)]:
            v = _interp_segment(a, b, t)
            assert 0.0 <= v <= 1.0

    # Off → On: ramps 0 → 1, monotonically non-decreasing
    assert _interp_segment(False, True, 0.0) == 0.0
    assert _interp_segment(False, True, 1.0) == 1.0
    vals_on = [_interp_segment(False, True, t) for t in ts]
    for i in range(len(vals_on) - 1):
        assert vals_on[i] <= vals_on[i + 1]

    # On → Off: ramps 1 → 0, monotonically non-increasing
    assert _interp_segment(True, False, 0.0) == 1.0
    assert _interp_segment(True, False, 1.0) == 0.0
    vals_off = [_interp_segment(True, False, t) for t in ts]
    for i in range(len(vals_off) - 1):
        assert vals_off[i] >= vals_off[i + 1]


def test_advance_morph_clamps():
    morph = DigitMorph(old_value=3, new_value=7, progress=0.0, complete=False)

    morph._advance(0.3, 2.0)
    assert abs(morph.progress - 0.6) < 1e-9
    assert not morph.complete

    # 0.6 + 0.6 = 1.2 → clamped to 1.0
    morph._advance(0.3, 2.0)
    assert morph.progress == 1.0
    assert morph.complete

    # No-op after complete
    morph._advance(1.0, 2.0)
    assert morph.progress == 1.0
    assert morph.complete


def test_digit_change_starts_morph():
    clock = MorphingClock()
    clock._digits = [1, 2, 3, 4]
    clock._morphs = [
        DigitMorph(old_value=d, new_value=d, progress=1.0, complete=True)
        for d in clock._digits
    ]

    # Reproduce what draw() does when digit 3 changes from 4 → 5
    new_digits = [1, 2, 3, 5]
    for i, (prev, curr) in enumerate(zip(clock._digits, new_digits)):
        if curr != prev and clock._morphs[i].complete:
            clock._morphs[i] = DigitMorph(
                old_value=prev, new_value=curr, progress=0.0, complete=False
            )
            clock._digits[i] = curr

    assert clock._morphs[3].progress == 0.0
    assert not clock._morphs[3].complete
    assert clock._morphs[3].old_value == 4
    assert clock._morphs[3].new_value == 5

    # Unchanged digits remain complete and at progress 1.0
    for i in range(3):
        assert clock._morphs[i].complete
        assert clock._morphs[i].progress == 1.0


def test_segment_lines_in_bounds():
    for col_x in DIGIT_COLS:
        segs = _segment_lines(col_x, DIGIT_Y, DIGIT_W, DIGIT_H)
        assert len(segs) == 7, f"Expected 7 segments for col_x={col_x}"
        for seg_idx, (p1, p2) in enumerate(segs):
            for label, (x, y) in [("p1", p1), ("p2", p2)]:
                assert 0 <= x <= 127, (
                    f"col_x={col_x} seg={seg_idx} {label} x={x} out of [0,127]"
                )
                assert 0 <= y <= 63, (
                    f"col_x={col_x} seg={seg_idx} {label} y={y} out of [0,63]"
                )


def test_render_frame_smoke():
    """_render_frame must complete without error; all draw calls stay within bounds."""
    class _Draw:
        def __init__(self):
            self.calls = []

        def line(self, coords, fill=1):
            for pt in coords:
                x, y = pt
                assert 0 <= x <= 127, f"line x={x} out of [0,127]"
                assert 0 <= y <= 63,  f"line y={y} out of [0,63]"
            self.calls.append(('line', coords))

        def point(self, coord, fill=1):
            x, y = coord
            assert 0 <= x <= 127, f"point x={x} out of [0,127]"
            assert 0 <= y <= 63,  f"point y={y} out of [0,63]"
            self.calls.append(('point', coord))

    class FakeOled:
        def __init__(self):
            self.draw = _Draw()
            self.cleared = False
            self.displayed = False

        def clear(self):
            self.cleared = True

        def display(self):
            self.displayed = True

        def draw_text(self, *a, **kw):
            pass

    clock = MorphingClock()
    oled = FakeOled()
    clock._render_frame(oled)

    assert oled.cleared
    assert oled.displayed
    assert len(oled.draw.calls) > 0


if __name__ == "__main__":
    test_glyph_table()
    test_interp_segment_bounds()
    test_advance_morph_clamps()
    test_digit_change_starts_morph()
    test_segment_lines_in_bounds()
    test_render_frame_smoke()
    print("ALL TESTS PASSED")
