"""Clock — large date and time display."""
import time
from pm_auto.libs.oled_page import OLEDPage
from .pixel_font import get_pixel_font

font = get_pixel_font()

SCREEN_W = 128
SCREEN_H = 64


class PageClock(OLEDPage):
    def __init__(self):
        super().__init__()

    def main(self, oled, data, config):
        now = time.localtime()
        oled.clear()

        # Date (top, medium)
        date_str = time.strftime("%a %b %d", now)
        oled.draw_text(date_str, 14, 5, size=14, font_path=font)

        # Time (center, large)
        time_str = time.strftime("%H:%M:%S", now)
        oled.draw_text(time_str, 10, 25, size=22, font_path=font)

        # Year (bottom, small)
        year_str = time.strftime("%Y", now)
        oled.draw_text(year_str, 48, 52, size=10, font_path=font)

        # Colon blink (hide the colon every other second for pulse effect)
        # Already handled by the seconds in the time string

        oled.display()
