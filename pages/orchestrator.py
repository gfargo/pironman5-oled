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
import random
from pm_auto.libs.oled_page import OLEDPage

# Import info pages
from .mix import PageMix
from .docker_health import PageDockerHealth
from .network_status import PageNetwork
from .nvme_health import PageNVMeHealth
from .backup_status import PageBackupStatus
from .cpu_memory import PageCpuMemory
from .temperature import PageTemperature
from .plane_stats import PagePlaneStats
from .weather import PageWeather
from .github_activity import PageGithubActivity
from .clock import PageClock
from .octoprint_status import PageOctoprintStatus
from .portfolio_ticker import PagePortfolioTicker
from .budget_burn import PageBudgetBurn
from .sprint_board import PageSprintBoard
from .alert_page import PageAlert

# Import screensavers
from .screensavers import ALL_SCREENSAVERS

# Timing
INFO_DURATION = 12       # seconds per info page
SCREENSAVER_DURATION = 45  # seconds per screensaver
ALERT_DURATION = 5       # seconds per alert display cycle
PAUSE_FLAG = '/tmp/oled_paused'
SKIP_FLAG = '/tmp/oled_skip'
ALERT_FILE = '/tmp/oled_alert'


class PageOrchestrator(OLEDPage):
    def __init__(self):
        super().__init__()

        # Info pages in fixed display order
        self.info_pages = [
            PageClock(),
            PageCpuMemory(),
            PageDockerHealth(),
            PageTemperature(),
            PageNetwork(),
            PageNVMeHealth(),
            PageBackupStatus(),
            PageSprintBoard(),
            PagePortfolioTicker(),
            PageBudgetBurn(),
            PagePlaneStats(),
            PageWeather(),
            PageOctoprintStatus(),
            PageGithubActivity(),
            PageMix(),
        ]
        self.info_index = 0

        # Screensaver pool
        self.screensavers = [cls() for cls in ALL_SCREENSAVERS]
        self.current_screensaver = None

        # Alert page
        self.alert_page = PageAlert()

        # State machine
        self.mode = 'info'  # 'info', 'screensaver', or 'alert'
        self.mode_start = time.time()

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
            if not paused and elapsed >= INFO_DURATION:
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
            if not paused and elapsed >= SCREENSAVER_DURATION:
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
