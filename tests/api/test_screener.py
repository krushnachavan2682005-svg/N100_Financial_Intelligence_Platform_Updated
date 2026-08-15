from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_screener_valid():
    res = client.get("/api/v1/screener?min_roe=15.0")
    assert res.status_code == 200
    # Assuming standard behavior, the subset returned matches
    assert isinstance(res.json(), list)


def test_screener_invalid():
    res = client.get("/api/v1/screener?max_de=-1")
    assert res.status_code == 400
