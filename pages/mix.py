"""
OLED Page: Mix (Home Page)
Shows all network interfaces with per-interface icons, cycling between them.
CPU and Temp always visible at the bottom.

Layout (128×64):
  ┌──────────────────────┐
  │ [wifi] 192.168.0.105 │  (cycles: wlan, tailscale, eth)
  │                      │
  │ [cpu] CPU    [temp]  │
  │       12%    TEMP    │
  │                37°C  │
  └──────────────────────┘
"""
from itertools import islice
import time

from pm_auto.libs.utils import get_icon, get_font
from pm_auto.libs.oled_page import OLEDPage

font = get_font('UbuntuSans-Regular.ttf')

ethernet_icon = get_icon('icon_lan_20.png')
wifi_icon = get_icon('icon_wifi_20.png')
net_icon = get_icon('icon_network_20.png')
cpu_icon = get_icon('icon_cpu_24.png')
temp_icon = get_icon('icon_temperature_24.png')
error_icon = get_icon('icon_error_20.png')

# Interfaces to display (in priority order), skip docker/veth
SKIP_PREFIXES = ('br-', 'docker', 'veth', 'lo')


class PageMix(OLEDPage):
    def __init__(self):
        super().__init__()
        self.ip_index = 0
        self.ip_num = 0
        self.cycle_time_start = 0

    def _get_display_ips(self, ips):
        """Filter to meaningful interfaces only."""
        if not ips:
            return {}
        return {k: v for k, v in ips.items()
                if not any(k.startswith(p) for p in SKIP_PREFIXES)}

    def _get_icon_for_interface(self, interface):
        """Return the appropriate icon for a network interface."""
        if interface.startswith(('eth', 'en')):
            return ethernet_icon
        elif interface.startswith(('wlan', 'wl')):
            return wifi_icon
        elif interface.startswith('tailscale'):
            return net_icon  # network icon for tailscale
        return net_icon

    def _get_label_for_interface(self, interface):
        """Short label for interface type."""
        if interface.startswith(('wlan', 'wl')):
            return 'W'
        elif interface.startswith(('eth', 'en')):
            return 'E'
        elif interface.startswith('tailscale'):
            return 'T'
        return '?'

    def main(self, oled, data, config):
        scroll_interval = config.get('scroll_interval', 5)
        temperature_unit = config.get('temperature_unit', 'C')

        ips = self._get_display_ips(data.get('ips', {}))

        cpu_temp_c = data.get("cpu_temperature", 0)
        cpu_temp_f = cpu_temp_c * 9 / 5 + 32
        cpu_usage = data.get("cpu_percent", 0)
        if cpu_usage >= 100:
            cpu_usage = 100

        temp = cpu_temp_c if temperature_unit == 'C' else cpu_temp_f
        temp = round(temp, 1)

        oled.clear()

        # IP section — cycles between all valid interfaces
        if len(ips) == 0:
            oled.draw_icon(error_icon, 0, 0, scale=1, invert=False, dither=False, threshold=50)
            oled.draw_text('NO NETWORK', 22, 0, size=14, font_path=font)
        else:
            ip_list = list(ips.items())

            if self.ip_num != len(ip_list):
                self.ip_index = 0
                self.cycle_time_start = time.time()
                self.ip_num = len(ip_list)

            if time.time() - self.cycle_time_start >= scroll_interval:
                self.cycle_time_start = time.time()
                self.ip_index += 1
                if self.ip_index >= len(ip_list):
                    self.ip_index = 0

            interface, ip = ip_list[self.ip_index]
            icon = self._get_icon_for_interface(interface)
            oled.draw_icon(icon, 0, 0, scale=1, invert=False, dither=False, threshold=80)
            oled.draw_text(f'{ip}', 22, 0, size=14, font_path=font)

            # Show interface count indicator (e.g., "1/3")
            oled.draw_text(f'{self.ip_index+1}/{len(ip_list)}', 108, 0, size=10, font_path=font)

        # CPU
        oled.draw_icon(cpu_icon, 0, 25, scale=1, invert=False)
        oled.draw_text('CPU', 28, 25, size=10, font_path=font)
        oled.draw_text(f"{cpu_usage}%", 25, 35, size=14, font_path=font)

        # Temp
        oled.draw_icon(temp_icon, 68, 25, scale=1, invert=False)
        oled.draw_text('TEMP', 91, 25, size=10, font_path=font)
        oled.draw_text(f"{int(temp):d}\u00b0{temperature_unit}", 89, 35, size=14, font_path=font)

        oled.display()
