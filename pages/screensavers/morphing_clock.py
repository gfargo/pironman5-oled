"""Morphing clock — HH:MM with smooth 7-segment digit transitions and a breathing pulse."""
import math
import time
from dataclasses import dataclass

SCREEN_W = 128
SCREEN_H = 64

DIGIT_W = 20
DIGIT_H = 36
DIGIT_Y = (SCREEN_H - DIGIT_H) // 2  # 14

# X positions for H_tens, H_units, M_tens, M_units
# Layout: |13..33| 3px |36..56| 8px(colon) |72..92| 3px |95..115|
DIGIT_COLS = [13, 36, 72, 95]
COLON_CX = 64  # centre x; equidistant between H2 end (56) and M1 start (72)

MORPH_SPEED = 2.0     # progress per second → ~0.5 s transition
PULSE_SPEED = math.pi  # rad/s → 0.5 Hz breathing cycle

# 7-segment masks, indexed 0-9, order: (a, b, c, d, e, f, g)
# a=top horiz, b=top-right vert, c=bot-right vert,
# d=bot horiz, e=bot-left vert, f=top-left vert, g=mid horiz
SEGMENTS = [
    (True,  True,  True,  True,  True,  True,  False),  # 0
    (False, True,  True,  False, False, False, False),   # 1
    (True,  True,  False, True,  True,  False, True),    # 2
    (True,  True,  True,  True,  False, False, True),    # 3
    (False, True,  True,  False, False, True,  True),    # 4
    (True,  False, True,  True,  False, True,  True),    # 5
    (True,  False, True,  True,  True,  True,  True),    # 6
    (True,  True,  True,  False, False, False, False),   # 7
    (True,  True,  True,  True,  True,  True,  True),    # 8
    (True,  True,  True,  True,  False, True,  True),    # 9
]


def _segment_lines(x, y, w, h):
    """Return 7 segment endpoint pairs for a digit cell at (x, y) of size (w, h).

    Order: [a(top), b(top-right), c(bot-right), d(bottom), e(bot-left), f(top-left), g(middle)]
    Each entry is ((x1, y1), (x2, y2)).
    """
    m = y + h // 2
    return [
        ((x + 2, y),         (x + w - 2, y)),          # a: top
        ((x + w, y + 2),     (x + w,     m - 2)),       # b: top-right
        ((x + w, m + 2),     (x + w,     y + h - 2)),   # c: bot-right
        ((x + 2, y + h),     (x + w - 2, y + h)),       # d: bottom
        ((x,     m + 2),     (x,         y + h - 2)),   # e: bot-left
        ((x,     y + 2),     (x,         m - 2)),        # f: top-left
        ((x + 2, m),         (x + w - 2, m)),            # g: middle
    ]


def _interp_segment(on_old, on_new, t):
    """Segment presence (0.0–1.0) at morph progress t.

    Both on → 1.0; both off → 0.0; off→on → t; on→off → 1-t.
    Result always in [0, 1].
    """
    if on_old and on_new:
        return 1.0
    if not on_old and not on_new:
        return 0.0
    if not on_old and on_new:
        return float(t)
    return 1.0 - float(t)


@dataclass
class DigitMorph:
    old_value: int
    new_value: int
    progress: float = 1.0
    complete: bool = True

    def _advance(self, dt, morph_speed):
        """Advance morph progress; clamp to 1.0 and mark complete when done."""
        if self.complete:
            return
        self.progress = min(1.0, self.progress + dt * morph_speed)
        if self.progress >= 1.0:
            self.complete = True


class MorphingClock:
    def __init__(self):
        self.reset()

    def reset(self):
        self._last_time = time.time()
        self._pulse_phase = 0.0
        now = time.localtime()
        h, m = now.tm_hour, now.tm_min
        self._digits = [h // 10, h % 10, m // 10, m % 10]
        self._morphs = [
            DigitMorph(old_value=d, new_value=d, progress=1.0, complete=True)
            for d in self._digits
        ]

    def draw(self, oled):
        now_t = time.time()
        dt = min(now_t - self._last_time, 0.1)
        self._last_time = now_t

        self._pulse_phase += PULSE_SPEED * dt

        now = time.localtime()
        h, m = now.tm_hour, now.tm_min
        new_digits = [h // 10, h % 10, m // 10, m % 10]

        for i, (prev, curr) in enumerate(zip(self._digits, new_digits)):
            if curr != prev and self._morphs[i].complete:
                self._morphs[i] = DigitMorph(
                    old_value=prev,
                    new_value=curr,
                    progress=0.0,
                    complete=False,
                )
                self._digits[i] = curr

        for morph in self._morphs:
            morph._advance(dt, MORPH_SPEED)

        self._render_frame(oled)

    def _render_frame(self, oled):
        oled.clear()

        pulse = math.sin(self._pulse_phase)
        # Breathing: trim 1px from each segment end when pulse dips below threshold
        tip_trim = 1 if pulse < -0.6 else 0

        for col_x, morph in zip(DIGIT_COLS, self._morphs):
            segs = _segment_lines(col_x, DIGIT_Y, DIGIT_W, DIGIT_H)
            old_mask = SEGMENTS[morph.old_value]
            new_mask = SEGMENTS[morph.new_value]
            t = morph.progress

            for seg_idx, (p1, p2) in enumerate(segs):
                presence = _interp_segment(old_mask[seg_idx], new_mask[seg_idx], t)
                if presence < 0.04:
                    continue

                x1, y1 = p1
                x2, y2 = p2
                cxs = (x1 + x2) / 2.0
                cys = (y1 + y2) / 2.0
                dx = (x2 - x1) * presence / 2.0
                dy = (y2 - y1) * presence / 2.0
                trim = tip_trim if presence >= 0.99 else 0

                if dx != 0:  # horizontal segment
                    ax1 = max(0, min(127, int(cxs - dx) + trim))
                    ay  = max(0, min(63,  int(cys)))
                    ax2 = max(0, min(127, int(cxs + dx) - trim))
                    if ax1 > ax2:
                        continue
                    oled.draw.line([(ax1, ay), (ax2, ay)], fill=1)
                    if ay + 1 <= 63:
                        oled.draw.line([(ax1, ay + 1), (ax2, ay + 1)], fill=1)
                elif dy != 0:  # vertical segment
                    ax  = max(0, min(127, int(cxs)))
                    ay1 = max(0, min(63,  int(cys - dy) + trim))
                    ay2 = max(0, min(63,  int(cys + dy) - trim))
                    if ay1 > ay2:
                        continue
                    oled.draw.line([(ax, ay1), (ax, ay2)], fill=1)
                    if ax + 1 <= 127:
                        oled.draw.line([(ax + 1, ay1), (ax + 1, ay2)], fill=1)

        # Colon: two 2×2 dot squares centred at COLON_CX
        c_top = DIGIT_Y + DIGIT_H // 3
        c_bot = DIGIT_Y + 2 * DIGIT_H // 3
        for cy in (c_top, c_bot):
            oled.draw.point((COLON_CX - 1, cy),     fill=1)
            oled.draw.point((COLON_CX,     cy),     fill=1)
            oled.draw.point((COLON_CX - 1, cy + 1), fill=1)
            oled.draw.point((COLON_CX,     cy + 1), fill=1)

        oled.display()
