import sqlite3
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    conn = sqlite3.connect("nifty100.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO peer_percentiles (company_id, peer_group_name, metric, value, percentile_rank, year) VALUES (1, 'TestGroup', 'roe', 15.0, 50, 2024)"
        )
        conn.commit()
    except:
        pass
    conn.close()


def test_get_peers():
    res = client.get("/api/v1/peers/TestGroup")
    assert res.status_code == 200


def test_get_peers_404():
    res = client.get("/api/v1/peers/UnknownGroup123")
    assert res.status_code == 404


def test_compare_peers():
    res = client.get("/api/v1/companies/TCS/peers/compare")
    assert res.status_code == 200
    assert "radar_dataset" in res.json()
