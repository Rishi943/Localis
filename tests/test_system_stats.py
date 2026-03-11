import pytest
from fastapi.testclient import TestClient

def test_system_stats_returns_expected_fields(monkeypatch):
    """GET /api/system-stats returns the required JSON schema."""
    import psutil

    monkeypatch.setattr(psutil, "cpu_percent", lambda interval=None: 34.2)
    mock_mem = type("M", (), {"used": 11_400_000_000, "total": 16_000_000_000})()
    monkeypatch.setattr(psutil, "virtual_memory", lambda: mock_mem)

    from app.main import app
    client = TestClient(app)
    resp = client.get("/api/system-stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "cpu_pct" in data
    assert "ram_used_gb" in data
    assert "ram_total_gb" in data
    assert "vram_used_gb" in data
    assert "vram_total_gb" in data
    assert abs(data["cpu_pct"] - 34.2) < 0.01
    assert abs(data["ram_used_gb"] - 11.4) < 0.1

def test_system_stats_vram_falls_back_to_zero(monkeypatch):
    """VRAM returns 0.0 when the NVML handle raises an exception."""
    import app.main as main_module

    # Patch _NVML_OK to True but make the handle lookup raise
    monkeypatch.setattr(main_module, "_NVML_OK", True)

    class FakePynvml:
        @staticmethod
        def nvmlDeviceGetHandleByIndex(idx):
            raise Exception("no GPU handle")

    monkeypatch.setattr(main_module, "_pynvml", FakePynvml())

    from app.main import app
    client = TestClient(app)
    resp = client.get("/api/system-stats")
    assert resp.status_code == 200
    assert resp.json()["vram_used_gb"] == 0.0
    assert resp.json()["vram_total_gb"] == 0.0
