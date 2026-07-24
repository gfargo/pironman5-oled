"""Bundled pixel font — keeps OLED text consistent regardless of the host's system fonts.

VT323 (SIL OFL) is bundled under fonts/ and preferred over whatever
UbuntuSans build a given Pi OS image happens to ship.
"""
import os

FONT_FILENAME = 'VT323-Regular.ttf'
_BUNDLED_PATH = os.path.join(os.path.dirname(__file__), 'fonts', FONT_FILENAME)


def get_pixel_font():
    """Return a path to a TTF suitable for draw_text(..., font_path=...).

    Prefers the bundled font; falls back to pm_auto's system font lookup
    if the bundled file is ever missing (e.g. a stripped-down deploy).
    """
    if os.path.exists(_BUNDLED_PATH):
        return _BUNDLED_PATH
    from pm_auto.libs.utils import get_font
    return get_font('UbuntuSans-Regular.ttf')
