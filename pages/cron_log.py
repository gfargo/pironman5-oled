"""
Pure parsing of journalctl CRON log lines into per-job pass/fail results.

Kept free of `pm_auto` and `subprocess` so `parse_cron_log()` can be
unit-tested headless — same split as `oled_config.py`'s `resolve_config()`.
`pages/cron_status.py` is the only place that shells out to `journalctl` and
can't be exercised outside the real Pi.

Cron itself doesn't record a job's exit status in the log — only that it ran.
The one signal journalctl gives us for "something went wrong" is that crond
mails (or, with no MTA configured, discards-and-logs) any stdout/stderr the
job produced. Our cron scripts are silent on success, so a CMD line followed
by a MAIL/info line for the same CRON[pid] means the job produced output —
treated here as a failure. A CMD line with no follow-up is a clean pass.
"""
import re

_CRON_LINE = re.compile(
    r'^\w{3}\s+\d{1,2}\s+(?P<time>\d{2}:\d{2}:\d{2})\s+\S+\s+CRON\[(?P<pid>\d+)\]:'
    r'\s+\([^)]*\)\s+(?P<action>CMD|MAIL|info)\s+\((?P<detail>.*)\)\s*$'
)


def _job_name(command):
    """Reduce a CMD line's shell command to a short job name (script basename, no extension)."""
    parts = command.split()
    for part in reversed(parts):
        if part.endswith('.py') or '/' in part:
            return part.rsplit('/', 1)[-1].removesuffix('.py')
    return parts[-1] if parts else command


def parse_cron_log(text, limit=4):
    """Parse raw `journalctl -t CRON` output into the last `limit` job results.

    Returns a list of {'time': 'HH:MM', 'command': str, 'ok': bool} dicts,
    most recent run first. Lines that don't match the CRON log format are
    ignored — never raises.
    """
    entries = []
    pid_to_index = {}
    for raw_line in (text or '').splitlines():
        m = _CRON_LINE.match(raw_line.strip())
        if not m:
            continue
        pid = m.group('pid')
        action = m.group('action')
        if action == 'CMD':
            entries.append({
                'time': m.group('time')[:5],
                'command': _job_name(m.group('detail')),
                'ok': True,
            })
            pid_to_index[pid] = len(entries) - 1
        elif pid in pid_to_index:
            entries[pid_to_index[pid]]['ok'] = False

    return list(reversed(entries))[:limit]
