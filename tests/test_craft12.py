"""Static presentation contract checks; not medical validation."""
from pathlib import Path
WEB=Path(__file__).resolve().parents[1]/'web'
def test_craft_style_available_on_both_workspaces(client,monkeypatch):
    for mode in ('engineering','review'):
        monkeypatch.setenv('WAVEASSURE_WORKSPACE_MODE',mode)
        r=client.get('/')
        assert r.status_code==200
        assert '/static/craft.css' in r.text
    r=client.get('/static/craft.css')
    assert r.status_code==200 and len(r.content)>1000
def test_compact_navigation_has_accessible_labels():
    s=(WEB/'index.html').read_text(encoding='utf-8')
    for name in ('Workbench','Unblinded review practice','Records','Assurance log'):
        assert f'aria-label="{name}"' in s
    assert 'aria-current' in (WEB/'app.js').read_text(encoding='utf-8')
def test_no_external_styles_or_animated_medical_data():
    s=(WEB/'craft.css').read_text(encoding='utf-8')
    assert 'body::before { display: none; }' in s
    assert 'prefers-reduced-motion: reduce' in s
    for token in ('@import','url(http:','url(https:'):
        assert token not in s
    assert "getPropertyValue('--wave-ecg')" in (WEB/'app.js').read_text(encoding='utf-8')
