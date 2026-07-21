"""Pure Tailscale status parsing — no pm_auto dependency, safe to import in tests."""
import json
import re

MAX_NAME_LEN = 7
_PING_LATENCY_RE = re.compile(r'in (\d+(?:\.\d+)?)ms')


def parse_peers(raw_json):
    """Parse `tailscale status --json` output into peer rows.

    Returns a list of dicts: {name, online, latency}. `name` is the full
    hostname (not truncated) so callers can still use it to address the
    peer (e.g. `tailscale ping <name>`); truncate only for display.
    `latency` starts as None here; callers that ping peers separately fill
    it in afterward. Malformed/empty input yields an empty list rather than
    raising, so a broken `tailscale` CLI degrades to an empty page instead
    of a crash.
    """
    try:
        data = json.loads(raw_json)
    except (TypeError, ValueError):
        return []

    if not isinstance(data, dict):
        return []

    peers = []
    for peer in data.get('Peer', {}).values():
        name = peer.get('HostName') or peer.get('DNSName', '').split('.')[0]
        if not name:
            continue
        peers.append({
            'name': name,
            'online': bool(peer.get('Online', False)),
            'latency': None,
        })

    peers.sort(key=lambda p: (not p['online'], p['name']))
    return peers


def truncate_name(name, max_len=MAX_NAME_LEN):
    """Shorten a peer name for display on the fixed-width OLED row."""
    return name[:max_len]


def parse_ping_latency(ping_output):
    """Extract round-trip ms from `tailscale ping -c 1` output, or None."""
    if not ping_output:
        return None
    match = _PING_LATENCY_RE.search(ping_output)
    if not match:
        return None
    return float(match.group(1))


def should_refetch(last_fetch, now, interval=30):
    """True when the cached peer list is stale and should be re-fetched."""
    return now - last_fetch >= interval
