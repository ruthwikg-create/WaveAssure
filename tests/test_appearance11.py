"""Engineering-only appearance regressions; not clinical performance testing."""
import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / 'web'


def _palette(block):
    return dict(re.findall(r'(--[\w-]+):\s*(#[0-9a-fA-F]{6})', block))


def _luminance(h):
    rgb = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
    return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))


def _contrast(a, b):
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + .05) / (low + .05)


def test_accessible_palette_for_both_themes():
    css = (WEB / 'experience.css').read_text(encoding='utf-8')
    dark = _palette(css.split(':root[data-theme="light"]')[0])
    light = _palette(css.split(':root[data-theme="light"]')[1].split('html {')[0])
    combinations = (
        ('--text', '--panel'), ('--muted', '--panel'), ('--subtle', '--panel'),
        ('--muted', '--panel2'), ('--accent', '--panel'),
        ('--accent-contrast', '--accent'), ('--warn-text', '--warn-bg'),
        ('--accent-quiet', '--accent-soft'),
    )
    for name, palette in (('dark', dark), ('light', light)):
        for foreground, background in combinations:
            assert _contrast(palette[foreground], palette[background]) >= 4.5, (
                name, foreground, background
            )


def test_theme_controls_and_accessible_motion_on_both_workspaces():
    theme = (WEB / 'theme.js').read_text(encoding='utf-8')
    for name in ('index.html', 'review.html'):
        html = (WEB / name).read_text(encoding='utf-8')
        assert '/static/theme.js' in html
        assert '/static/experience.css' in html
        assert 'id="themeSelect"' in html
        assert 'value="system"' in html and 'value="light"' in html and 'value="dark"' in html
        assert 'id="motionToggle"' in html and 'aria-pressed=' in html
        assert 'role="group" aria-label="Appearance preferences"' in html
    assert 'prefers-reduced-motion: reduce' in theme
    assert "localStorage.setItem" in theme
    assert 'document.documentElement' in theme
    assert '@media (prefers-reduced-motion:reduce)' in (WEB / 'experience.css').read_text(encoding='utf-8')


def test_theme_only_redisplays_measurements_without_modifying_samples():
    app = (WEB / 'app.js').read_text(encoding='utf-8')
    assert "getPropertyValue('--wave-ecg')" in app
    assert "getPropertyValue('--grid')" in app
    assert "window.addEventListener('waveassure:appearance'" in app
    assert 'pilotWaveforms.forEach' in app
    assert 'showPilotCase(pilotCase)' not in app  # Would erase unfinished reviewer form.
    review = (WEB / 'review.js').read_text(encoding='utf-8')
    assert "canvas.waveAssureData=w" in review
    assert 'waveassure:appearance' in review
    assert 'ctx.clearRect(' in review


def test_static_theme_assets_served_under_security_headers(client):
    for path in ('theme.js', 'experience.css', 'review-theme.css'):
        r = client.get('/static/' + path)
        assert r.status_code == 200
        assert r.headers['x-content-type-options'] == 'nosniff'
        assert len(r.content) > 100


def test_no_external_theme_network_dependency_or_unsafe_inline_js():
    theme = (WEB / 'theme.js').read_text(encoding='utf-8')
    for suspect in ('http://', 'https://', 'eval(', 'new Function(', 'document.write('):
        assert suspect not in theme
    html = (WEB / 'index.html').read_text(encoding='utf-8')
    review = (WEB / 'review.html').read_text(encoding='utf-8')
    assert '<script src="/static/theme.js"></script>' in html
    assert '<script src="/static/theme.js"></script>' in review
