"""Regression tests for the localhost Windows launcher startup sequence.

Tests simulate port/health conditions; no network service is started.
Passing tests do not establish safety or clinical readiness.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'run-local.py'
BATCH = ROOT / 'scripts' / 'start-windows.bat'


def load_runner():
    spec = importlib.util.spec_from_file_location('waveassure_local_start', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_windows_batch_does_not_launch_browser_before_server():
    text = BATCH.read_text(encoding='utf-8')
    assert 'scripts\\run-local.py' in text
    assert 'start "" http://127.0.0.1:8000' not in text
    assert 'Python/Uvicorn error printed above' in text


def test_health_gate_waits_for_real_waveassure_health(monkeypatch, capsys):
    r = load_runner()
    events = []
    checks = iter([None, None, {
        'status': 'ok', 'version': '0.21.0',
        'intended_use': 'research_only', 'workspace_mode': 'engineering'}])
    monkeypatch.setattr(r, 'probe_health', lambda: next(checks))
    monkeypatch.setattr(r.time, 'sleep', lambda _: events.append('poll'))
    monkeypatch.setattr(r.webbrowser, 'open', lambda uri, new=0: events.append(('open',uri)) or True)
    r.open_browser_when_ready()
    assert events == ['poll', 'poll', ('open', 'http://127.0.0.1:8000')]
    assert 'READY' in capsys.readouterr().out


def test_health_gate_will_not_open_if_not_healthy(monkeypatch):
    r = load_runner()
    opens = []
    monkeypatch.setattr(r, 'probe_health', lambda: None)
    monkeypatch.setattr(r.time, 'sleep', lambda _: None)
    monkeypatch.setattr(r.webbrowser, 'open', lambda uri, new=0: opens.append(uri))
    r.open_browser_when_ready()
    assert opens == []


def test_foreign_service_on_8000_fails_closed(monkeypatch, capsys):
    r = load_runner()
    monkeypatch.setattr(r, 'port_in_use', lambda: True)
    monkeypatch.setattr(r, 'probe_health', lambda: None)
    assert r.main() == 1
    assert 'port 8000 is occupied' in capsys.readouterr().out.lower()


def test_existing_engineering_server_opens_without_starting_another(monkeypatch):
    r = load_runner()
    opened = []
    monkeypatch.setattr(r, 'port_in_use', lambda: True)
    monkeypatch.setattr(r, 'probe_health', lambda: {
        'status': 'ok', 'version': '0.21.0',
        'intended_use': 'research_only', 'workspace_mode': 'engineering'})
    monkeypatch.setattr(r.webbrowser, 'open', lambda url, new=0: opened.append(url))
    assert r.main() == 0
    assert opened == ['http://127.0.0.1:8000']


def test_launch_is_loopback_only_and_runs_in_foreground(monkeypatch):
    r = load_runner()
    uvicorn_calls = []
    threads = []
    monkeypatch.setattr(r, 'port_in_use', lambda: False)

    class DummyThread:
        def __init__(self, *, target, name, daemon):
            assert target == r.open_browser_when_ready
            assert daemon
            threads.append(name)

        def start(self): pass

    monkeypatch.setattr(r.threading, 'Thread', DummyThread)
    monkeypatch.setitem(sys.modules, 'uvicorn',
                        SimpleNamespace(run=lambda *args,**kwargs: uvicorn_calls.append((args, kwargs))))
    assert r.main() == 0
    assert threads == ['WaveAssureHealthGate']
    assert uvicorn_calls == [(('waveassure.api:app',),
                              {'host':'127.0.0.1','port':8000,'log_level':'info'})]
