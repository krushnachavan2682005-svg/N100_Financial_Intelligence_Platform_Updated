from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_get_valuation():
    res = client.get("/api/v1/valuation/TCS")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
