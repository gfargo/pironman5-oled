"""Screensaver: Bouncing DVD Logo — the classic corner-hit dopamine machine.

Hit counter persists across page switches for the entire uptime of the
pironman5 service. Uses a simple file in /tmp so the count survives
orchestrator cycles but resets on reboot (which is the desired behavior —
it tracks "uptime hits").
"""
import time
import os
from pm_auto.libs.oled_page import OLEDPage
from .pixel_font import get_pixel_font

font = get_pixel_font()

# Display: 128x64
# "DVD" text is roughly 30x14 pixels at size 14
LOGO_W = 26
LOGO_H = 12
SCREEN_W = 128
SCREEN_H = 64

HITS_FILE = '/tmp/dvd_bounce_hits'


def _load_hits():
    """Load persisted hit count from tmpfs."""
    try:
        with open(HITS_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def _save_hits(count):
    """Persist hit count to tmpfs (survives page switches, resets on reboot)."""
    try:
        with open(HITS_FILE, 'w') as f:
            f.write(str(count))
    except OSError:
        pass


class PageScreensaverDVD(OLEDPage):
    def __init__(self):
        super().__init__()
        self.x = 10.0
        self.y = 20.0
        self.vx = 1.5
        self.vy = 1.0
        self.hits = _load_hits()
        self.last_time = 0
        self._save_counter = 0  # batch saves to reduce I/O

    def main(self, oled, data, config):
        now = time.time()

        # Animate at consistent speed regardless of call frequency
        dt = now - self.last_time if self.last_time > 0 else 0.05
        self.last_time = now

        # Cap dt to avoid jumps after page switch
        dt = min(dt, 0.1)

        # Move
        speed = 60  # pixels per second
        self.x += self.vx * speed * dt
        self.y += self.vy * speed * dt

        # Bounce
        hit = False
        if self.x <= 0:
            self.x = 0
            self.vx = abs(self.vx)
            hit = True
        elif self.x >= SCREEN_W - LOGO_W:
            self.x = SCREEN_W - LOGO_W
            self.vx = -abs(self.vx)
            hit = True

        if self.y <= 0:
            self.y = 0
            self.vy = abs(self.vy)
            hit = True
        elif self.y >= SCREEN_H - LOGO_H:
            self.y = SCREEN_H - LOGO_H
            self.vy = -abs(self.vy)
            hit = True

        if hit:
            self.hits += 1
            # Slightly randomize angle on bounce for variety
            self.vx += (hash(str(now)) % 5 - 2) * 0.1
            self.vy += (hash(str(now * 2)) % 5 - 2) * 0.1
            # Clamp velocity
            self.vx = max(-2.0, min(2.0, self.vx))
            self.vy = max(-1.5, min(1.5, self.vy))
            # Persist every 10 hits to reduce disk writes
            self._save_counter += 1
            if self._save_counter >= 10:
                _save_hits(self.hits)
                self._save_counter = 0

        oled.clear()
        oled.draw_text("DVD", int(self.x), int(self.y), size=14, font_path=font)

        # Corner hit counter in tiny text
        if self.hits > 0:
            oled.draw_text(f"{self.hits}", 118, 56, size=8, font_path=font)

        oled.display()
