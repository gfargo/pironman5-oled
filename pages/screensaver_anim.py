"""Screensaver: Random animations — starfield, matrix rain, sine wave, life."""
import time
import math
import random
from pm_auto.libs.oled_page import OLEDPage
from .pixel_font import get_pixel_font

font = get_pixel_font()

SCREEN_W = 128
SCREEN_H = 64


class PageScreensaverAnim(OLEDPage):
    def __init__(self):
        super().__init__()
        self.last_time = 0
        self.anim_start = 0
        self.current_anim = 0
        self.anim_duration = 5  # seconds per animation before switching
        self.state = {}
        self._init_anim()

    def _init_anim(self):
        """Initialize state for current animation."""
        self.anim_start = time.time()
        self.state = {}

        if self.current_anim == 0:
            # Starfield
            self.state['stars'] = [
                {'x': random.uniform(0, SCREEN_W), 'y': random.uniform(0, SCREEN_H),
                 'speed': random.uniform(20, 80)}
                for _ in range(30)
            ]
        elif self.current_anim == 1:
            # Matrix rain
            self.state['columns'] = [
                {'x': i * 8, 'y': random.randint(-20, SCREEN_H), 'speed': random.uniform(30, 80),
                 'chars': [chr(random.randint(33, 126)) for _ in range(8)]}
                for i in range(16)
            ]
        elif self.current_anim == 2:
            # Sine wave
            self.state['phase'] = 0.0
        elif self.current_anim == 3:
            # Bouncing particles
            self.state['particles'] = [
                {'x': random.uniform(10, 118), 'y': random.uniform(10, 54),
                 'vx': random.uniform(-50, 50), 'vy': random.uniform(-50, 50)}
                for _ in range(12)
            ]

    def _next_anim(self):
        """Advance to next animation."""
        self.current_anim = (self.current_anim + 1) % 4
        self._init_anim()

    def main(self, oled, data, config):
        now = time.time()
        dt = now - self.last_time if self.last_time > 0 else 0.05
        self.last_time = now
        dt = min(dt, 0.1)

        # Switch animation every N seconds
        if now - self.anim_start > self.anim_duration:
            self._next_anim()

        oled.clear()

        if self.current_anim == 0:
            self._draw_starfield(oled, dt)
        elif self.current_anim == 1:
            self._draw_matrix(oled, dt)
        elif self.current_anim == 2:
            self._draw_sine(oled, dt)
        elif self.current_anim == 3:
            self._draw_particles(oled, dt)

        oled.display()

    def _draw_starfield(self, oled, dt):
        """Stars flying toward viewer from center."""
        for star in self.state['stars']:
            star['x'] += (star['x'] - 64) * dt * 1.5
            star['y'] += (star['y'] - 32) * dt * 1.5
            star['speed'] += dt * 20

            # Wrap around
            if star['x'] < 0 or star['x'] > SCREEN_W or star['y'] < 0 or star['y'] > SCREEN_H:
                star['x'] = 64 + random.uniform(-10, 10)
                star['y'] = 32 + random.uniform(-10, 10)
                star['speed'] = random.uniform(20, 40)

            # Draw as dot (using a tiny text character)
            size = 1 if star['speed'] < 50 else 2
            ix, iy = int(star['x']), int(star['y'])
            if 0 <= ix < SCREEN_W and 0 <= iy < SCREEN_H:
                oled.draw_text(".", ix, iy, size=8 + size * 2, font_path=font)

    def _draw_matrix(self, oled, dt):
        """Falling character columns."""
        for col in self.state['columns']:
            col['y'] += col['speed'] * dt

            # Draw 3 visible characters in the column
            for i in range(3):
                cy = int(col['y']) - i * 10
                if 0 <= cy < SCREEN_H:
                    char = col['chars'][(int(col['y'] / 10) + i) % len(col['chars'])]
                    # Top char is brightest (drawn), others fade (smaller)
                    sz = 10 if i == 0 else 8
                    oled.draw_text(char, col['x'], cy, size=sz, font_path=font)

            # Reset column when it goes off screen
            if col['y'] > SCREEN_H + 20:
                col['y'] = random.randint(-30, -10)
                col['speed'] = random.uniform(30, 80)
                col['chars'] = [chr(random.randint(33, 126)) for _ in range(8)]

    def _draw_sine(self, oled, dt):
        """Flowing sine wave across the screen."""
        self.state['phase'] = self.state.get('phase', 0) + dt * 3

        for x in range(0, SCREEN_W, 2):
            y = 32 + int(20 * math.sin((x / 20.0) + self.state['phase']))
            y2 = 32 + int(12 * math.sin((x / 12.0) + self.state['phase'] * 1.5 + 1))
            if 0 <= y < SCREEN_H:
                oled.draw_text(".", x, y, size=8, font_path=font)
            if 0 <= y2 < SCREEN_H:
                oled.draw_text(".", x, y2, size=8, font_path=font)

    def _draw_particles(self, oled, dt):
        """Bouncing particles."""
        for p in self.state['particles']:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt

            if p['x'] <= 0 or p['x'] >= SCREEN_W - 4:
                p['vx'] *= -1
                p['x'] = max(0, min(SCREEN_W - 4, p['x']))
            if p['y'] <= 0 or p['y'] >= SCREEN_H - 4:
                p['vy'] *= -1
                p['y'] = max(0, min(SCREEN_H - 4, p['y']))

            oled.draw_text("o", int(p['x']), int(p['y']), size=8, font_path=font)
