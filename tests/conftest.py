"""Shared test setup: stubs the `pm_auto` package (not installed in CI/dev
outside the real Pironman5 device) so `pages/*` and `pages/screensavers/*`
can be imported and exercised headlessly.
"""
import os
import sys
import types

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def _install_pm_auto_stub():
    if 'pm_auto' in sys.modules:
        return

    pm_auto = types.ModuleType('pm_auto')
    pm_auto_libs = types.ModuleType('pm_auto.libs')

    oled_page_mod = types.ModuleType('pm_auto.libs.oled_page')

    class OLEDPage:
        def __init__(self, *args, **kwargs):
            pass

    oled_page_mod.OLEDPage = OLEDPage

    utils_mod = types.ModuleType('pm_auto.libs.utils')

    def get_font(name, *args, **kwargs):
        return name

    def get_icon(name, *args, **kwargs):
        return object()

    def format_bytes(n, *args, **kwargs):
        return str(n)

    utils_mod.get_font = get_font
    utils_mod.get_icon = get_icon
    utils_mod.format_bytes = format_bytes

    pm_auto.libs = pm_auto_libs
    pm_auto_libs.oled_page = oled_page_mod
    pm_auto_libs.utils = utils_mod

    sys.modules['pm_auto'] = pm_auto
    sys.modules['pm_auto.libs'] = pm_auto_libs
    sys.modules['pm_auto.libs.oled_page'] = oled_page_mod
    sys.modules['pm_auto.libs.utils'] = utils_mod


_install_pm_auto_stub()
