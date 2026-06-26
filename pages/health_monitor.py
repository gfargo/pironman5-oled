"""
Health Monitor — background checker that triggers OLED alerts.

Run as a cron job or systemd timer (every 5 minutes):
  */5 * * * * /opt/pironman5/venv/bin/python3 /path/to/health_monitor.py

Checks:
  1. Docker: any containers unhealthy or exited unexpectedly
  2. Plane API: reachable on localhost:8080
  3. Backup age: latest backup on watch < 2 hours old
  4. Disk: NVMe usage > 85%

If any check fails, writes /tmp/oled_alert with the issue.
If all checks pass, removes /tmp/oled_alert (clears the alert).
"""
import subprocess
import json
import time
import os
import urllib.request

ALERT_FILE = '/tmp/oled_alert'


def check_docker():
    """Check for unhealthy or crashed containers."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'],
            capture_output=True, text=True, timeout=5)
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) == 2:
                name, status = parts
                if 'unhealthy' in status.lower():
                    return f"Container {name} unhealthy"
        # Check for unexpected exits
        result_all = subprocess.run(
            ['docker', 'ps', '-a', '--filter', 'status=exited',
             '--format', '{{.Names}}\t{{.Status}}'],
            capture_output=True, text=True, timeout=5)
        for line in result_all.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) == 2:
                name, status = parts
                # Ignore migrators and one-shot containers
                if 'migrator' in name or 'pi-db-init' in name:
                    continue
                # Only alert on recent exits (within last 30 min)
                if 'minutes ago' in status or 'seconds ago' in status:
                    return f"Container {name} crashed"
    except Exception:
        pass
    return None


def check_plane():
    """Check if Plane API is reachable."""
    try:
        req = urllib.request.Request('http://localhost:8080/api/instances/',
                                     headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                return None
        return "Plane API not responding"
    except Exception:
        return "Plane API unreachable"


def check_disk():
    """Check NVMe disk usage."""
    try:
        result = subprocess.run(['df', '/'], capture_output=True, text=True, timeout=3)
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            pct = int(lines[1].split()[4].replace('%', ''))
            if pct > 85:
                return f"Disk {pct}% full"
    except Exception:
        pass
    return None


def check_backup():
    """Check if last backup from watch is recent (via watch hub API)."""
    try:
        with urllib.request.urlopen('http://watch:8090/api/stats', timeout=5) as resp:
            data = json.loads(resp.read())
            backup = data.get('backup')
            if backup and backup.get('age_hours', 99) > 2:
                return f"Backup stale ({backup['age_hours']}h old)"
    except Exception:
        # Watch might be offline — not critical enough for alert
        pass
    return None


def main():
    # Run all checks
    checks = [
        ('docker', check_docker),
        ('plane', check_plane),
        ('disk', check_disk),
        ('backup', check_backup),
    ]

    for name, check_fn in checks:
        issue = check_fn()
        if issue:
            # Write alert
            alert = {
                'message': issue,
                'severity': 'critical' if name in ('docker', 'plane') else 'warning',
                'source': name,
                'since': str(time.time()),
            }
            # Don't overwrite existing alert unless it's a different issue
            existing = None
            try:
                with open(ALERT_FILE, 'r') as f:
                    existing = json.loads(f.read())
            except (FileNotFoundError, json.JSONDecodeError):
                pass

            if not existing or existing.get('message') != issue:
                with open(ALERT_FILE, 'w') as f:
                    json.dump(alert, f)
            return  # Show first critical issue found

    # All clear — remove alert if it exists
    if os.path.exists(ALERT_FILE):
        os.remove(ALERT_FILE)


if __name__ == '__main__':
    main()
