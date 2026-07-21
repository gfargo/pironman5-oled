"""
Alert Page — shown when a critical condition is detected.
Interrupts normal rotation until the alert clears.

Alerts are triggered by writing JSON to /tmp/oled_alert:
  {"message": "Plane API down", "severity": "critical", "since": "1718000000"}

The orchestrator checks this file every frame and shows this page
instead of the normal rotation when an alert is active.

To clear: rm /tmp/oled_alert
To trigger from a script: echo '{"message":"...","severity":"critical"}' > /tmp/oled_alert
"""
import json
import os
import time
import math
from pm_auto.libs.oled_page import OLEDPage
from .pixel_font import get_pixel_font

font = get_pixel_font()

ALERT_FILE = '/tmp/oled_alert'
SCREEN_W = 128
SCREEN_H = 64


class PageAlert(OLEDPage):
    def __init__(self):
        super().__init__()
        self._tick = 0

    def get_alert(self):
        """Read alert data from file. Returns None if no alert."""
        try:
            with open(ALERT_FILE, 'r') as f:
                data = json.loads(f.read())
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def main(self, oled, data, config):
        alert = self.get_alert()
        if not alert:
            return

        self._tick += 1
        oled.clear()

        # Flashing border effect (draw border every other second)
        severity = alert.get('severity', 'warning')
        if severity == 'critical' and self._tick % 4 < 2:
            # Draw border
            oled.draw.rectangle([(0, 0), (SCREEN_W - 1, SCREEN_H - 1)], outline=1, fill=0)
            oled.draw.rectangle([(1, 1), (SCREEN_W - 2, SCREEN_H - 2)], outline=1, fill=0)

        # Header with severity
        header = "!! ALERT !!" if severity == 'critical' else "! WARNING !"
        oled.draw_text(header, 20, 3, size=12, font_path=font)

        # Message (wrap to fit 128px width)
        message = alert.get('message', 'Unknown issue')
        # Split into lines of ~20 chars
        words = message.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + " " + word) > 20:
                lines.append(current_line)
                current_line = word
            else:
                current_line = (current_line + " " + word).strip()
        if current_line:
            lines.append(current_line)

        for i, line in enumerate(lines[:3]):
            oled.draw_text(line, 5, 20 + i * 12, size=11, font_path=font)

        # Duration since alert
        since = alert.get('since', 0)
        if since:
            elapsed = int(time.time() - float(since))
            if elapsed > 3600:
                duration = f"{elapsed // 3600}h {(elapsed % 3600) // 60}m ago"
            elif elapsed > 60:
                duration = f"{elapsed // 60}m ago"
            else:
                duration = f"{elapsed}s ago"
            oled.draw_text(duration, 70, 54, size=9, font_path=font)

        oled.display()
