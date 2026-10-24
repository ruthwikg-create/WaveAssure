import pytest
@pytest.fixture
def client(tmp_path,monkeypatch):
    from waveassure import storage
    monkeypatch.setattr(storage,'DB_PATH',tmp_path/'tests.sqlite3')
    from fastapi.testclient import TestClient
    from waveassure.api import app
    with TestClient(app) as c:yield c
