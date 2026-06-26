"""Ocean waves — layered sine waves creating a water surface effect."""
import math

SCREEN_W = 128
SCREEN_H = 64


class OceanWaves:
    def __init__(self):
        self.t = 0.0
        # Multiple wave layers with different speeds, amplitudes, frequencies
        self.waves = [
            {'amp': 8, 'freq': 0.04, 'speed': 1.2, 'y_offset': 30},
            {'amp': 5, 'freq': 0.06, 'speed': 0.8, 'y_offset': 38},
            {'amp': 4, 'freq': 0.08, 'speed': 1.5, 'y_offset': 45},
            {'amp': 3, 'freq': 0.10, 'speed': 0.6, 'y_offset': 52},
        ]

    def step(self):
        self.t += 0.06

    def render(self, oled):
        oled.clear()

        for wave in self.waves:
            amp = wave['amp']
            freq = wave['freq']
            speed = wave['speed']
            base_y = wave['y_offset']

            prev_y = None
            for x in range(SCREEN_W):
                # Combine two sine waves for more natural look
                y1 = math.sin(x * freq + self.t * speed) * amp
                y2 = math.sin(x * freq * 1.7 + self.t * speed * 0.7 + 1.3) * (amp * 0.4)
                y = int(base_y + y1 + y2)

                # Clamp
                y = max(0, min(SCREEN_H - 1, y))

                # Draw the wave line
                oled.draw.point((x, y), fill=1)

                # Fill below with sparse dots for depth effect (only deepest layer)
                if wave == self.waves[-1]:
                    for fill_y in range(y + 2, SCREEN_H, 3):
                        if (x + fill_y) % 5 == 0:
                            oled.draw.point((x, fill_y), fill=1)

                prev_y = y

        oled.display()

    def reset(self):
        self.__init__()

    def draw(self, oled):
        self.step()
        self.render(oled)
