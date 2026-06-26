"""Network — merged Platform + Tailscale view. Shows all nodes with status."""
import subprocess
import json
import time
from pm_auto.libs.oled_page import OLEDPage
from pm_auto.libs.utils import get_font

font = get_font('UbuntuSans-Regular.ttf')


class PageNetwork(OLEDPage):
    def __init__(self):
        super().__init__()
        self._cache = {}
        self._tick = 0

    def _get_status(self):
        self._tick += 1
        if self._cache and self._tick % 15 != 0:
            return self._cache

        nodes = {}

        # compass (local)
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read()) // 1000
            result = subprocess.run(['docker', 'ps', '-q'],
                                    capture_output=True, text=True, timeout=3)
            ctr = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            nodes['compass'] = {'online': True, 'temp': temp, 'ctr': ctr, 'ts': True}
        except Exception:
            nodes['compass'] = {'online': True, 'temp': 0, 'ctr': 0, 'ts': True}

        # Tailscale peers
        try:
            result = subprocess.run(['tailscale', 'status', '--json'],
                                    capture_output=True, text=True, timeout=5)
            ts_data = json.loads(result.stdout)
            for peer in ts_data.get('Peer', {}).values():
                hostname = peer.get('HostName', '')
                online = peer.get('Online', False)
                if hostname == 'watch':
                    nodes['watch'] = {'online': online, 'temp': 0, 'ctr': 0, 'ts': online}
                elif hostname == 'macbook-pro-gf':
                    nodes['loom'] = {'online': online, 'temp': 0, 'ctr': 0, 'ts': online}
                elif hostname == 'iphone-14-pro':
                    nodes['iphone'] = {'online': online, 'temp': 0, 'ctr': 0, 'ts': online}
        except Exception:
            pass

        # Try to get watch stats via hub API
        if 'watch' in nodes and nodes['watch']['online']:
            try:
                import urllib.request
                with urllib.request.urlopen('http://watch:8090/api/stats', timeout=3) as resp:
                    wd = json.loads(resp.read())
                    nodes['watch']['temp'] = wd.get('temp', 0)
                    nodes['watch']['ctr'] = wd.get('containers', 0)
            except Exception:
                pass

        self._cache = nodes
        return self._cache

    def main(self, oled, data, config):
        nodes = self._get_status()

        oled.clear()

        # Compact header
        online = sum(1 for n in nodes.values() if n['online'])
        oled.draw_text('NETWORK', 0, 0, size=10, font_path=font)
        oled.draw_text(f"{online}/{len(nodes)} up", 80, 0, size=10, font_path=font)
        oled.draw_bar_graph_horizontal(100, 0, 12, 128, 1)

        # Node rows: name | ts | temp | containers
        y = 15
        for name, info in nodes.items():
            if y > 60:
                break
            ts_dot = "*" if info.get('ts') else "x"
            if info['online']:
                temp_s = f"{info['temp']}C" if info['temp'] > 0 else "--"
                ctr_s = f"{info['ctr']}c" if info['ctr'] > 0 else ""
                oled.draw_text(f"{ts_dot} {name[:7]:<7} {temp_s:<4} {ctr_s}", 0, y, size=10, font_path=font)
            else:
                oled.draw_text(f"{ts_dot} {name[:7]:<7} offline", 0, y, size=10, font_path=font)
            y += 12

        oled.display()
