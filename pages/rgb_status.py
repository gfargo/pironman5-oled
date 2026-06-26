"""
RGB Status — updates Pironman5 LED color based on system health.

Run as a cron job or systemd timer (every 30 seconds):
  */1 * * * * /opt/pironman5/venv/bin/python3 /path/to/rgb_status.py

Colors:
  - Green (#00ff00): all healthy
  - Yellow (#ffaa00): warning (backup stale, disk filling)
  - Red (#ff0000): critical (containers down, Plane unreachable)
  - Blue (#0066ff): default/idle (no checks run yet)

Updates the pironman5 config via its HTTP dashboard API.
"""
import subprocess
import json
import os
import urllib.request

PIRONMAN_API = "http://localhost:34001"
ALERT_FILE = '/tmp/oled_alert'


def get_health_color():
    """Determine LED color based on system health."""
    # Critical: check if alert exists
    if os.path.exists(ALERT_FILE):
        try:
            with open(ALERT_FILE, 'r') as f:
                alert = json.loads(f.read())
                if alert.get('severity') == 'critical':
                    return '#ff0000'  # Red
                else:
                    return '#ffaa00'  # Yellow
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    # Check for unhealthy containers
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Status}}'],
            capture_output=True, text=True, timeout=5)
        if 'unhealthy' in result.stdout.lower():
            return '#ffaa00'  # Yellow
    except Exception:
        pass

    # All good
    return '#00ff00'  # Green


def set_led_color(color):
    """Update LED color via pironman5 dashboard API."""
    try:
        data = json.dumps({"rgb_color": color}).encode()
        req = urllib.request.Request(
            f"{PIRONMAN_API}/api/set-config",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST')
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        # Fallback: write directly to config and let pironman5 pick it up
        try:
            config_path = '/opt/pironman5/config.json'
            with open(config_path, 'r') as f:
                config = json.load(f)
            if config.get('system', {}).get('rgb_color') != color:
                config.setdefault('system', {})['rgb_color'] = color
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
        except Exception:
            pass


def main():
    color = get_health_color()
    set_led_color(color)


if __name__ == '__main__':
    main()
