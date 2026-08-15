from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "uptime_seconds" in data
    assert "db_row_counts" in data

    # Verify all expected tables are in db_row_counts
    expected_tables = [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "financial_ratios",
        "peer_percentiles",
    ]
    for t in expected_tables:
        assert t in data["db_row_counts"]
        # Assumes tables exist and query didn't throw OperationalError
        assert isinstance(data["db_row_counts"][t], int)
