import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def patch_ha(monkeypatch):
    import app.assist as assist_mod
    monkeypatch.setattr(assist_mod, '_ha_url', 'http://ha.local:8123')
    monkeypatch.setattr(assist_mod, '_ha_token', 'fake-token')
    monkeypatch.setattr(assist_mod, '_light_entity', 'light.test_light')
    monkeypatch.setattr(assist_mod, 'ha_call_service',
                        AsyncMock(return_value={'result': 'ok'}))

def test_light_toggle():
    r = client.post('/assist/light/toggle')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

def test_light_brightness():
    r = client.post('/assist/light/brightness', json={'value': 60})
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

def test_light_brightness_out_of_range():
    r = client.post('/assist/light/brightness', json={'value': 150})
    assert r.status_code == 422

def test_light_color():
    r = client.post('/assist/light/color', json={'rgb': [255, 100, 0]})
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

def test_light_kelvin():
    r = client.post('/assist/light/kelvin', json={'kelvin': 4000})
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

def test_controls_503_when_ha_not_configured(monkeypatch):
    import app.assist as assist_mod
    monkeypatch.setattr(assist_mod, '_ha_url', '')
    r = client.post('/assist/light/toggle')
    assert r.status_code == 503
