"""Unit tests for the pure Tailscale status parsing helpers.

These test pages/_tailscale_util.py directly, which has no `pm_auto`
import (unlike pages/tailscale_peers.py), so it can be imported here
without the pm_auto package installed.
"""
import json
import sys

sys.path.insert(0, sys.path[0].replace('/tests', '/pages'))
from _tailscale_util import parse_peers, parse_ping_latency, should_refetch


SAMPLE_JSON = json.dumps({
    "Peer": {
        "key1": {"HostName": "watch", "DNSName": "watch.tailnet.ts.net.", "Online": True},
        "key2": {"HostName": "loom", "DNSName": "loom.tailnet.ts.net.", "Online": False},
        "key3": {"HostName": "iphone14pro", "DNSName": "iphone14pro.tailnet.ts.net.", "Online": True},
    }
})


def test_parse_peers_mixed_online_offline():
    peers = parse_peers(SAMPLE_JSON)
    assert len(peers) == 3
    names = {p['name'] for p in peers}
    assert 'watch' in names
    assert 'loom' in names

    by_name = {p['name']: p for p in peers}
    assert by_name['watch']['online'] is True
    assert by_name['loom']['online'] is False


def test_parse_peers_online_sorted_first():
    peers = parse_peers(SAMPLE_JSON)
    # offline peers should sort after online peers
    online_flags = [p['online'] for p in peers]
    first_offline = online_flags.index(False) if False in online_flags else len(online_flags)
    assert all(online_flags[:first_offline])


def test_parse_peers_empty_peer_dict():
    assert parse_peers(json.dumps({"Peer": {}})) == []


def test_parse_peers_no_peer_key():
    assert parse_peers(json.dumps({})) == []


def test_parse_peers_malformed_json_returns_empty():
    assert parse_peers("not valid json{{{") == []
    assert parse_peers(None) == []
    assert parse_peers(json.dumps([1, 2, 3])) == []


def test_parse_peers_name_truncation():
    raw = json.dumps({
        "Peer": {"k": {"HostName": "a-very-long-hostname", "Online": True}}
    })
    peers = parse_peers(raw)
    assert peers[0]['name'] == 'a-very-'
    assert len(peers[0]['name']) == 7


def test_parse_peers_falls_back_to_dnsname():
    raw = json.dumps({
        "Peer": {"k": {"HostName": "", "DNSName": "myhost.tailnet.ts.net.", "Online": True}}
    })
    peers = parse_peers(raw)
    assert peers[0]['name'] == 'myhost'


def test_parse_peers_skips_peer_with_no_name():
    raw = json.dumps({
        "Peer": {"k": {"HostName": "", "DNSName": "", "Online": True}}
    })
    assert parse_peers(raw) == []


def test_parse_ping_latency_direct():
    output = "pong from peer (100.1.2.3) via 192.168.1.5:41641 in 5ms"
    assert parse_ping_latency(output) == 5.0


def test_parse_ping_latency_relay():
    output = "pong from peer (100.1.2.3) via DERP(nyc) in 42ms"
    assert parse_ping_latency(output) == 42.0


def test_parse_ping_latency_no_match():
    assert parse_ping_latency("some unrelated output") is None


def test_parse_ping_latency_empty():
    assert parse_ping_latency("") is None
    assert parse_ping_latency(None) is None


def test_should_refetch_within_window():
    assert should_refetch(last_fetch=100.0, now=110.0, interval=30) is False


def test_should_refetch_after_window():
    assert should_refetch(last_fetch=100.0, now=131.0, interval=30) is True


def test_should_refetch_exact_boundary():
    assert should_refetch(last_fetch=100.0, now=130.0, interval=30) is True
