"""Tests for pages/oled_config.py's pure resolve_config() logic.

resolve_config() takes no dependency on pm_auto or yaml — it operates on
plain dicts — so it's testable headless, unlike load_config() which touches
disk/yaml and needs the real orchestrator environment.
"""
import sys

sys.path.insert(0, sys.path[0].replace('/tests', '/pages'))
from oled_config import DEFAULT_CONFIG, resolve_config, consume_flag

VALID_PAGES = ['clock', 'cpu_memory', 'mix', 'weather']


def test_enable_disable_only_listed_pages_returned():
    resolved = resolve_config({'pages': ['clock', 'mix']}, VALID_PAGES)
    assert resolved['pages'] == ['clock', 'mix']


def test_ordering_matches_input_order():
    resolved = resolve_config({'pages': ['mix', 'clock', 'weather']}, VALID_PAGES)
    assert resolved['pages'] == ['mix', 'clock', 'weather']


def test_unknown_page_name_dropped_not_raised():
    resolved = resolve_config({'pages': ['clock', 'bogus_page']}, VALID_PAGES)
    assert resolved['pages'] == ['clock']
    assert 'bogus_page' not in resolved['pages']


def test_duplicate_page_name_deduped():
    resolved = resolve_config({'pages': ['clock', 'mix', 'clock']}, VALID_PAGES)
    assert resolved['pages'] == ['clock', 'mix']


def test_missing_pages_key_uses_default():
    resolved = resolve_config({}, DEFAULT_CONFIG['pages'])
    assert resolved['pages'] == DEFAULT_CONFIG['pages']


def test_none_raw_config_uses_defaults():
    resolved = resolve_config(None, DEFAULT_CONFIG['pages'])
    assert resolved['pages'] == DEFAULT_CONFIG['pages']
    assert resolved['timing'] == DEFAULT_CONFIG['timing']


def test_empty_pages_list_uses_default():
    resolved = resolve_config({'pages': []}, DEFAULT_CONFIG['pages'])
    assert resolved['pages'] == DEFAULT_CONFIG['pages']


def test_all_unknown_pages_falls_back_to_default():
    resolved = resolve_config({'pages': ['bogus_a', 'bogus_b']}, VALID_PAGES)
    assert resolved['pages'] == DEFAULT_CONFIG['pages']


def test_missing_timing_keys_use_defaults():
    resolved = resolve_config({'timing': {'info_duration': 20}}, VALID_PAGES)
    assert resolved['timing']['info_duration'] == 20
    assert resolved['timing']['screensaver_duration'] == DEFAULT_CONFIG['timing']['screensaver_duration']
    assert resolved['timing']['alert_duration'] == DEFAULT_CONFIG['timing']['alert_duration']


def test_invalid_timing_value_falls_back_to_default():
    resolved = resolve_config({'timing': {'info_duration': 'not-a-number'}}, VALID_PAGES)
    assert resolved['timing']['info_duration'] == DEFAULT_CONFIG['timing']['info_duration']


def test_missing_timing_key_entirely_uses_defaults():
    resolved = resolve_config({'pages': ['clock']}, VALID_PAGES)
    assert resolved['timing'] == DEFAULT_CONFIG['timing']


def test_string_timing_value_coerced_to_int():
    resolved = resolve_config({'timing': {'info_duration': '20'}}, VALID_PAGES)
    assert resolved['timing']['info_duration'] == 20
    assert isinstance(resolved['timing']['info_duration'], int)


def test_consume_flag_returns_true_and_removes_existing_file(tmp_path):
    flag = tmp_path / 'oled_reload'
    flag.write_text('')
    assert consume_flag(str(flag)) is True
    assert not flag.exists()


def test_consume_flag_returns_false_when_file_absent(tmp_path):
    flag = tmp_path / 'oled_reload'
    assert consume_flag(str(flag)) is False
