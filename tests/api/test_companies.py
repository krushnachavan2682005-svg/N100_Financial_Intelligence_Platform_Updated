import pytest
import os
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_tearsheet():
    # Setup dummy pdf for tearsheet test
    os.makedirs("reports/tearsheets", exist_ok=True)
    with open("reports/tearsheets/TCS_tearsheet.pdf", "wb") as f:
        f.write(b"%PDF-1.4 dummy pdf content")

    yield

    # Teardown
    if os.path.exists("reports/tearsheets/TCS_tearsheet.pdf"):
        os.remove("reports/tearsheets/TCS_tearsheet.pdf")


def test_get_companies():
    # Basic get
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Database has 92 companies
    # It might have slightly less or more if dirty, but let's just check length > 0
    assert len(data) > 0

    # Check fields
    first = data[0]
    expected_keys = [
        "id",
        "company_name",
        "broad_sector",
        "sub_sector",
        "market_cap_crore",
        "roe_pct",
        "roce_pct",
        "nse",
    ]
    for k in expected_keys:
        assert k in first


def test_get_companies_search():
    # Test search query
    response = client.get("/api/v1/companies?search=TCS")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any("TCS" in c["nse"] or "TCS" in c["company_name"] for c in data)


def test_get_companies_market_cap():
    response = client.get("/api/v1/companies?market_cap_category=Large Cap")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["market_cap_crore"] >= 20000


def test_get_company_profile():
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["nse"] == "TCS"
    assert "latest_ratios" in data


def test_get_company_profile_not_found():
    response = client.get("/api/v1/companies/INVALIDTICKER123")
    assert response.status_code == 404


def test_get_company_pl():
    response = client.get("/api/v1/companies/TCS/pl")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "sales" in data[0]


def test_get_company_bs():
    response = client.get("/api/v1/companies/TCS/bs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_company_cashflow():
    response = client.get("/api/v1/companies/TCS/cashflow")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_company_ratios():
    response = client.get("/api/v1/companies/TCS/ratios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_company_tearsheet():
    response = client.get("/api/v1/companies/TCS/tearsheet")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

    # Test not found
    response_404 = client.get("/api/v1/companies/NOTFOUND/tearsheet")
    assert response_404.status_code == 404
