"""Tests for pages/pixel_font.py — the bundled-font resolver.

get_pixel_font() has no dependency on pm_auto when the bundled file is
present, so it's testable headless without the real orchestrator environment.
"""
import os
import sys

sys.path.insert(0, sys.path[0].replace('/tests', '/pages'))
import pixel_font
from pixel_font import FONT_FILENAME, get_pixel_font

PAGES_DIR = os.path.dirname(os.path.abspath(pixel_font.__file__))


def test_bundled_font_file_exists_and_is_non_empty():
    font_path = os.path.join(PAGES_DIR, 'fonts', FONT_FILENAME)
    assert os.path.exists(font_path)
    assert os.path.getsize(font_path) > 0


def test_get_pixel_font_returns_bundled_path():
    path = get_pixel_font()
    assert os.path.exists(path)
    assert path.endswith(FONT_FILENAME)


def test_pil_can_load_bundled_font():
    try:
        from PIL import ImageFont
    except ImportError:
        return
    font = ImageFont.truetype(get_pixel_font(), 12)
    assert font.getbbox("Hello") is not None
