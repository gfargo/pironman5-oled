"""Binary clock — current time displayed as pulsing binary dots."""
import time
import math

SCREEN_W = 128
SCREEN_H = 64


class BinaryClock:
    def __init__(self):
        self.pulse_t = 0.0

    def step(self):
        self.pulse_t += 0.1

    def _draw_dot(self, oled, x, y, active, size=4):
        """Draw a dot — filled if active, outline if inactive."""
        if active:
            # Filled circle (approximation with rectangle + corners)
            for dy in range(size):
                for dx in range(size):
                    # Crude circle mask
                    cx = dx - size / 2 + 0.5
                    cy = dy - size / 2 + 0.5
                    if cx * cx + cy * cy <= (size / 2) * (size / 2):
                        oled.draw.point((x + dx, y + dy), fill=1)
        else:
            # Just corner dots for outline
            oled.draw.point((x + size // 2, y), fill=1)
            oled.draw.point((x + size // 2, y + size - 1), fill=1)
            oled.draw.point((x, y + size // 2), fill=1)
            oled.draw.point((x + size - 1, y + size // 2), fill=1)

    def render(self, oled):
        oled.clear()

        now = time.localtime()
        h, m, s = now.tm_hour, now.tm_min, now.tm_sec

        # Split into digits: H1 H2 : M1 M2 : S1 S2
        digits = [h // 10, h % 10, m // 10, m % 10, s // 10, s % 10]
        # Max bits needed: [2, 4, 3, 4, 3, 4] (tens digit of hours max 2, etc.)
        max_bits = [2, 4, 3, 4, 3, 4]

        from pm_auto.libs.utils import get_font
        font = get_font('UbuntuSans-Regular.ttf')

        # Labels
        labels = ["H", "", "M", "", "S", ""]
        col_width = 18
        start_x = 14
        dot_size = 5
        row_spacing = 10
        start_y = 18

        # Draw column headers
        for col, label in enumerate(labels):
            x = start_x + col * col_width
            if label:
                oled.draw_text(label, x + 1, 4, size=9, font_path=font)

        # Draw separator colons
        oled.draw_text(":", start_x + 2 * col_width - 5, 30, size=14, font_path=font)
        oled.draw_text(":", start_x + 4 * col_width - 5, 30, size=14, font_path=font)

        # Draw binary columns (MSB at top)
        for col in range(6):
            x = start_x + col * col_width
            val = digits[col]
            bits = max_bits[col]
            for bit in range(bits):
                y = start_y + (3 - bit) * row_spacing  # MSB at top
                active = bool(val & (1 << bit))
                # Pulse active dots
                if active:
                    pulse = 0.8 + 0.2 * math.sin(self.pulse_t + col * 0.5)
                    if pulse > 0.5:
                        self._draw_dot(oled, x, y, True, dot_size)
                else:
                    self._draw_dot(oled, x, y, False, dot_size)

        oled.display()

    def reset(self):
        self.__init__()

    def draw(self, oled):
        self.step()
        self.render(oled)
