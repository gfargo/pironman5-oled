"""Tests for pages/cron_log.py's pure parse_cron_log() logic.

parse_cron_log() takes no dependency on pm_auto or subprocess — it operates
on a plain string — so it's testable headless, unlike the journalctl-shelling
code in cron_status.py which needs the real orchestrator environment.
"""
import sys

sys.path.insert(0, sys.path[0].replace('/tests', '/pages'))
from cron_log import parse_cron_log


PASSING_JOB = (
    "Jul 20 09:00:01 pi5 CRON[21345]: (pi) CMD "
    "(/opt/pironman5/venv/bin/python3 /home/gfargo/pironman5-oled/pages/rgb_status.py)"
)

FAILING_JOB = (
    "Jul 20 09:05:01 pi5 CRON[21400]: (pi) CMD "
    "(/opt/pironman5/venv/bin/python3 /home/gfargo/pironman5-oled/pages/health_monitor.py)\n"
    "Jul 20 09:05:02 pi5 CRON[21400]: (CRON) info (No MTA installed, discarding output)"
)


def test_clean_run_marked_ok():
    entries = parse_cron_log(PASSING_JOB)
    assert len(entries) == 1
    assert entries[0]['ok'] is True
    assert entries[0]['command'] == 'rgb_status'
    assert entries[0]['time'] == '09:00'


def test_run_with_output_marked_failed():
    entries = parse_cron_log(FAILING_JOB)
    assert len(entries) == 1
    assert entries[0]['ok'] is False
    assert entries[0]['command'] == 'health_monitor'


def test_mail_line_also_marks_failed():
    text = (
        "Jul 20 09:10:01 pi5 CRON[21500]: (pi) CMD (/path/to/backup.sh)\n"
        "Jul 20 09:10:03 pi5 CRON[21500]: (pi) MAIL "
        "(mailed 348 bytes of output but got status 0x4b00)"
    )
    entries = parse_cron_log(text)
    assert entries[0]['ok'] is False


def test_unrelated_log_lines_ignored():
    text = "Jul 20 09:00:01 pi5 systemd[1]: Started Session.\nnot a cron line at all"
    assert parse_cron_log(text) == []


def test_empty_and_none_input_returns_empty_list():
    assert parse_cron_log("") == []
    assert parse_cron_log(None) == []


def test_results_ordered_most_recent_first():
    text = PASSING_JOB + "\n" + FAILING_JOB
    entries = parse_cron_log(text)
    assert [e['command'] for e in entries] == ['health_monitor', 'rgb_status']


def test_limit_caps_number_of_entries():
    lines = "\n".join(
        f"Jul 20 09:0{i}:01 pi5 CRON[2000{i}]: (pi) CMD (/path/to/job{i}.py)"
        for i in range(6)
    )
    entries = parse_cron_log(lines, limit=3)
    assert len(entries) == 3
    assert entries[0]['command'] == 'job5'


def test_pid_reuse_does_not_alias_older_entry():
    text = (
        "Jul 20 08:00:01 pi5 CRON[999]: (pi) CMD (/path/to/first.py)\n"
        "Jul 20 09:00:01 pi5 CRON[999]: (pi) CMD (/path/to/second.py)\n"
        "Jul 20 09:00:02 pi5 CRON[999]: (CRON) info (No MTA installed, discarding output)"
    )
    entries = parse_cron_log(text)
    by_command = {e['command']: e['ok'] for e in entries}
    assert by_command['first'] is True
    assert by_command['second'] is False


def test_command_with_trailing_args_uses_script_basename():
    text = "Jul 20 09:00:01 pi5 CRON[1]: (pi) CMD (/usr/bin/python3 /opt/job.py --flag value)"
    entries = parse_cron_log(text)
    assert entries[0]['command'] == 'job'


def test_command_with_output_redirection_uses_script_basename():
    text = (
        "Jul 20 09:00:01 pi5 CRON[1]: (pi) CMD "
        "(/bin/bash /opt/backup.sh > /var/log/backup.log 2>&1)"
    )
    entries = parse_cron_log(text)
    assert entries[0]['command'] == 'backup.sh'
