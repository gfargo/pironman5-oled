#!/bin/bash
# deploy.sh — Install custom OLED pages into the pironman5 venv.
#
# Usage (on the Pi):
#   cd ~/pironman5-oled && git pull && bash deploy.sh
#
# Or remotely:
#   ssh compass 'cd ~/pironman5-oled && git pull && bash deploy.sh'
#
# What it does:
#   1. Nukes the existing custom pages directory (prevents stale files)
#   2. Copies all pages + screensavers into the pironman5 site-packages
#   3. Updates the pironman5 config to use the orchestrator
#   4. Restarts the pironman5 service
#
# Requirements:
#   - pironman5 installed at /opt/pironman5
#   - Python venv at /opt/pironman5/venv
#   - Run as root (or with sudo) for service restart

set -euo pipefail

PIRONMAN_ROOT="/opt/pironman5"
VENV_PACKAGES="$PIRONMAN_ROOT/venv/lib/python3.*/site-packages"
OLED_ADDON_PATH=$(echo $VENV_PACKAGES/pm_auto/addons/oled)
PAGES_DIR="$OLED_ADDON_PATH/pages"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[deploy] Pironman5 OLED page deployment"
echo "[deploy] Source: $SCRIPT_DIR"
echo "[deploy] Target: $PAGES_DIR"

# Verify pironman5 exists
if [ ! -d "$PIRONMAN_ROOT" ]; then
    echo "[deploy] ERROR: pironman5 not found at $PIRONMAN_ROOT"
    exit 1
fi

# Find the actual site-packages path (handles python version differences)
ACTUAL_PAGES=$(find "$PIRONMAN_ROOT/venv/lib" -path "*/pm_auto/addons/oled/pages" -type d 2>/dev/null | head -1)
if [ -z "$ACTUAL_PAGES" ]; then
    echo "[deploy] ERROR: Could not find pm_auto/addons/oled/pages in venv"
    exit 1
fi

echo "[deploy] Resolved target: $ACTUAL_PAGES"

# Step 1: Nuke existing custom pages (keep __init__.py backup)
echo "[deploy] Cleaning existing pages..."
find "$ACTUAL_PAGES" -name "*.py" -not -name "__init__.py" -delete 2>/dev/null || true
find "$ACTUAL_PAGES" -name "*.pyc" -delete 2>/dev/null || true
rm -rf "$ACTUAL_PAGES/__pycache__" 2>/dev/null || true
rm -rf "$ACTUAL_PAGES/screensavers/__pycache__" 2>/dev/null || true

# Step 2: Copy pages
echo "[deploy] Installing pages..."
cp "$SCRIPT_DIR/pages/"*.py "$ACTUAL_PAGES/"
mkdir -p "$ACTUAL_PAGES/screensavers"
cp "$SCRIPT_DIR/pages/screensavers/"*.py "$ACTUAL_PAGES/screensavers/"

# Step 3: Copy the pages __init__.py (registry)
cp "$SCRIPT_DIR/pages/__init__.py" "$ACTUAL_PAGES/__init__.py"

# Step 4: Update config to use orchestrator (idempotent)
CONFIG="$PIRONMAN_ROOT/config.json"
if [ -f "$CONFIG" ]; then
    if ! grep -q '"orchestrator"' "$CONFIG"; then
        echo "[deploy] Updating config to use orchestrator page..."
        python3 -c "
import json
with open('$CONFIG') as f: cfg = json.load(f)
cfg['system']['oled_pages'] = ['orchestrator']
cfg['system']['page_rotate_interval'] = 9999
with open('$CONFIG', 'w') as f: json.dump(cfg, f, indent=4)
print('[deploy] Config updated')
"
    else
        echo "[deploy] Config already uses orchestrator"
    fi
fi

# Step 5: Clear bytecache
echo "[deploy] Clearing bytecache..."
find "$ACTUAL_PAGES" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Step 6: Restart service
echo "[deploy] Restarting pironman5 service..."
systemctl restart pironman5 2>/dev/null || service pironman5 restart 2>/dev/null || true

echo "[deploy] Done! OLED should update within a few seconds."
