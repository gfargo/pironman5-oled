from .pixel_font import get_pixel_font
from pm_auto.libs.oled_page import OLEDPage

font = get_pixel_font()

class PagePowerOff(OLEDPage):
    def main(self, oled):
        oled.clear()
        oled.draw_text(f'POWER OFF', 64, 20, align='center', size=24, font_path=font)
        oled.display()
