"""
OLED Orchestrator — manages the info → screensaver → info flow.

This is the ONLY page registered in pironman5. It internally alternates
between info screens (12s each) and randomly-selected screensavers (45s).

Features:
  - Alert mode: interrupts rotation when /tmp/oled_alert exists (flashing border)
  - Adaptive timing: pages with no content skip faster (3s instead of 12s)
  - Pause/skip via button (file flags at /tmp/oled_paused, /tmp/oled_skip)
  - Try/except on all page renders (crashes skip instead of freeze)
"""
import time
import os
import sys
import random
import logging
import importlib
from pm_auto.libs.oled_page import OLEDPage

# Config
from .oled_config import DEFAULT_CONFIG, load_config, resolve_config, consume_flag

log = logging.getLogger(__name__)

CONFIG_PATH = '/opt/pironman5/oled-config.yaml'

# Timing defaults — overridden per-instance by oled-config.yaml, see resolve_config()
INFO_DURATION = DEFAULT_CONFIG['timing']['info_duration']
SCREENSAVER_DURATION = DEFAULT_CONFIG['timing']['screensaver_duration']
ALERT_DURATION = DEFAULT_CONFIG['timing']['alert_duration']
PAUSE_FLAG = '/tmp/oled_paused'
SKIP_FLAG = '/tmp/oled_skip'
ALERT_FILE = '/tmp/oled_alert'
RELOAD_FLAG = '/tmp/oled_reload'

# Name -> (module, class name), used to build self.info_pages from the resolved
# config. Kept as a lazy lookup table (rather than importing the classes
# directly) so `_build(reload_modules=True)` can `importlib.reload()` each
# module and pick up source edits without restarting the service.
INFO_PAGE_MODULES = {
    'clock': ('.clock', 'PageClock'),
    'cpu_memory': ('.cpu_memory', 'PageCpuMemory'),
    'docker_health': ('.docker_health', 'PageDockerHealth'),
    'temperature': ('.temperature', 'PageTemperature'),
    'network': ('.network_status', 'PageNetwork'),
    'tailscale_peers': ('.tailscale_peers', 'PageTailscalePeers'),
    'nvme_health': ('.nvme_health', 'PageNVMeHealth'),
    'backup_status': ('.backup_status', 'PageBackupStatus'),
    'cron_status': ('.cron_status', 'PageCronStatus'),
    'sprint_board': ('.sprint_board', 'PageSprintBoard'),
    'portfolio_ticker': ('.portfolio_ticker', 'PagePortfolioTicker'),
    'budget_burn': ('.budget_burn', 'PageBudgetBurn'),
    'plane_stats': ('.plane_stats', 'PagePlaneStats'),
    'weather': ('.weather', 'PageWeather'),
    'octoprint_status': ('.octoprint_status', 'PageOctoprintStatus'),
    'github_activity': ('.github_activity', 'PageGithubActivity'),
    'mix': ('.mix', 'PageMix'),
}
ALERT_PAGE_MODULE = ('.alert_page', 'PageAlert')


class PageOrchestrator(OLEDPage):
    def __init__(self):
        super().__init__()
        self._build(reload_modules=False)

        # State machine
        self.mode = 'info'  # 'info', 'screensaver', or 'alert'
        self.mode_start = time.time()

    def _import(self, modname, reload_modules):
        """Import (or re-import) `modname` relative to this package."""
        mod = sys.modules.get(__package__ + modname)
        if mod is None:
            mod = importlib.import_module(modname, package=__package__)
        elif reload_modules:
            mod = importlib.reload(mod)
        return mod

    def _build(self, reload_modules=False):
        """(Re)build page state from oled-config.yaml + page/screensaver modules.

        On `reload_modules=True`, re-imports every page/screensaver module so
        source edits go live without a service restart (see /tmp/oled_reload
        in main()). Builds into locals first — only assigned to self on
        success, so a bad edit can't leave the orchestrator half-rebuilt.
        """
        info_page_classes = {}
        for name, (modname, clsname) in INFO_PAGE_MODULES.items():
            mod = self._import(modname, reload_modules)
            info_page_classes[name] = getattr(mod, clsname)

        # Load + resolve oled-config.yaml (falls back to defaults on any failure)
        raw_config = load_config(CONFIG_PATH)
        resolved = resolve_config(raw_config, list(INFO_PAGE_MODULES.keys()))

        # Info pages, enabled/ordered per the resolved config
        info_pages = [info_page_classes[name]() for name in resolved['pages']]

        # Timing, per the resolved config
        info_duration = resolved['timing']['info_duration']
        screensaver_duration = resolved['timing']['screensaver_duration']
        alert_duration = resolved['timing']['alert_duration']

        # Screensaver pool — reload each submodule before the package's
        # __init__, so `ALL_SCREENSAVERS` picks up fresh classes.
        if reload_modules:
            for modname in list(sys.modules):
                if modname.startswith(__package__ + '.screensavers.'):
                    importlib.reload(sys.modules[modname])
        screensavers_pkg = self._import('.screensavers', reload_modules)
        screensavers = [cls() for cls in screensavers_pkg.ALL_SCREENSAVERS]

        # Alert page
        alert_mod = self._import(ALERT_PAGE_MODULE[0], reload_modules)
        alert_page = getattr(alert_mod, ALERT_PAGE_MODULE[1])()

        # Commit — only reached if nothing above raised.
        self.info_pages = info_pages
        self.info_index = 0
        self.info_duration = info_duration
        self.screensaver_duration = screensaver_duration
        self.alert_duration = alert_duration
        self.screensavers = screensavers
        self.current_screensaver = None
        self.alert_page = alert_page

    def _switch_to_screensaver(self):
        """Pick a random screensaver and start it."""
        self.mode = 'screensaver'
        self.mode_start = time.time()
        self.current_screensaver = random.choice(self.screensavers)
        self.current_screensaver.reset()

    def _switch_to_info(self):
        """Advance to next info page in sequence."""
        self.mode = 'info'
        self.mode_start = time.time()
        self.info_index = (self.info_index + 1) % len(self.info_pages)

    def main(self, oled, data, config):
        now = time.time()
        elapsed = now - self.mode_start

        # ── Alert check (highest priority) ─────────────────────
        has_alert = os.path.exists(ALERT_FILE)
        if has_alert and self.mode != 'alert':
            self.mode = 'alert'
            self.mode_start = now
            elapsed = 0

        # ── Check pause state ──────────────────────────────────
        paused = os.path.exists(PAUSE_FLAG)

        # ── Check skip signal ──────────────────────────────────
        if os.path.exists(SKIP_FLAG):
            try:
                os.remove(SKIP_FLAG)
            except OSError:
                pass
            if self.mode == 'alert':
                # Skip clears alert
                try:
                    os.remove(ALERT_FILE)
                except OSError:
                    pass
                self._switch_to_info()
            elif self.mode == 'screensaver':
                self._switch_to_info()
            else:
                self.info_index = (self.info_index + 1) % len(self.info_pages)
                self.mode_start = now
            return

        # ── Check reload signal ────────────────────────────────
        if consume_flag(RELOAD_FLAG):
            try:
                self._build(reload_modules=True)
                log.info("oled pages reloaded from %s", RELOAD_FLAG)
            except Exception:
                log.exception("oled reload failed — keeping current pages")
            self.mode = 'info'
            self.mode_start = now
            return

        # ── Alert mode ─────────────────────────────────────────
        if self.mode == 'alert':
            if not has_alert:
                # Alert cleared externally
                self._switch_to_info()
                return
            try:
                self.alert_page.main(oled, data, config)
            except Exception:
                pass
            return

        # ── Info mode ──────────────────────────────────────────
        if self.mode == 'info':
            if not paused and elapsed >= self.info_duration:
                self._switch_to_screensaver()
                return
            page = self.info_pages[self.info_index]
            try:
                page.main(oled, data, config)
            except Exception:
                self._switch_to_screensaver()
                return
            # Pause indicator
            if paused:
                oled.draw.point((126, 1), fill=1)
                oled.draw.point((127, 1), fill=1)
                oled.draw.point((126, 2), fill=1)
                oled.draw.point((127, 2), fill=1)
                oled.display()

        # ── Screensaver mode ───────────────────────────────────
        elif self.mode == 'screensaver':
            if not paused and elapsed >= self.screensaver_duration:
                self._switch_to_info()
                return
            if self.current_screensaver:
                try:
                    self.current_screensaver.draw(oled)
                except Exception:
                    oled.clear()
                    oled.display()
                    self._switch_to_info()
                    return
                if paused:
                    oled.draw.point((126, 1), fill=1)
                    oled.draw.point((127, 1), fill=1)
                    oled.draw.point((126, 2), fill=1)
                    oled.draw.point((127, 2), fill=1)
                    oled.display()
