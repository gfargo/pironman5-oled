"""
YAML config loading/resolution for the OLED orchestrator.

Kept free of `pm_auto` and safe to import without PyYAML installed, so the
resolution logic (`resolve_config`) can be unit-tested headless. `load_config`
is the only function that touches disk/yaml, and degrades to `None` on any
failure — callers fall back to `DEFAULT_CONFIG` in that case.
"""
import logging

log = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'pages': [
        'clock',
        'cpu_memory',
        'docker_health',
        'temperature',
        'network',
        'nvme_health',
        'backup_status',
        'sprint_board',
        'portfolio_ticker',
        'budget_burn',
        'plane_stats',
        'weather',
        'octoprint_status',
        'github_activity',
        'mix',
    ],
    'timing': {
        'info_duration': 12,
        'screensaver_duration': 45,
        'alert_duration': 5,
    },
}


def load_config(path):
    """Read and parse the YAML config file at `path`.

    Returns the parsed dict, or None if the file is missing, PyYAML isn't
    installed, or parsing fails. Never raises.
    """
    try:
        import yaml
    except ImportError:
        log.warning("PyYAML not installed — using default oled config")
        return None

    try:
        with open(path, 'r') as f:
            raw = yaml.safe_load(f)
    except FileNotFoundError:
        return None
    except OSError as e:
        log.warning("Could not read oled config %s: %s", path, e)
        return None
    except yaml.YAMLError as e:
        log.warning("Could not parse oled config %s: %s", path, e)
        return None

    if not isinstance(raw, dict):
        log.warning("oled config %s did not contain a mapping — ignoring", path)
        return None

    return raw


def _coerce_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def resolve_config(raw, valid_page_names):
    """Merge a raw config dict (or None) with defaults, dropping unknowns.

    `valid_page_names` is the list of page names the orchestrator knows how
    to instantiate. Unknown page names are warned about and skipped, never
    raised. Duplicate names are de-duped, keeping first occurrence. Timing
    values fall back to defaults if absent or non-numeric. If the resolved
    page list ends up empty, the default page list is used instead.
    """
    raw = raw or {}
    valid = set(valid_page_names)

    requested_pages = raw.get('pages')
    if not isinstance(requested_pages, list) or not requested_pages:
        requested_pages = DEFAULT_CONFIG['pages']

    resolved_pages = []
    seen = set()
    for name in requested_pages:
        if name in seen:
            log.warning("Duplicate page '%s' in oled config — skipping", name)
            continue
        if name not in valid:
            log.warning("Unknown page '%s' in oled config — skipping", name)
            continue
        seen.add(name)
        resolved_pages.append(name)

    if not resolved_pages:
        log.warning("oled config resolved to zero valid pages — using defaults")
        resolved_pages = list(DEFAULT_CONFIG['pages'])

    raw_timing = raw.get('timing')
    if not isinstance(raw_timing, dict):
        raw_timing = {}

    default_timing = DEFAULT_CONFIG['timing']
    timing = {
        'info_duration': _coerce_int(
            raw_timing.get('info_duration'), default_timing['info_duration']
        ),
        'screensaver_duration': _coerce_int(
            raw_timing.get('screensaver_duration'), default_timing['screensaver_duration']
        ),
        'alert_duration': _coerce_int(
            raw_timing.get('alert_duration'), default_timing['alert_duration']
        ),
    }

    return {
        'pages': resolved_pages,
        'timing': timing,
    }
