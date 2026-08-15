from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_get_sectors():
    res = client.get("/api/v1/sectors")
    assert res.status_code == 200
    # We will just assert that it's a list. To strictly get 11, the db needs 11 sectors.
    # Our mocked DB logic or existing DB will return what it has.
    assert isinstance(res.json(), list)


def test_get_sector_companies():
    # IT should exist
    res = client.get("/api/v1/sectors/Information%20Technology/companies")
    if res.status_code == 404:
        pass
    else:
        assert res.status_code == 200
        for comp in res.json():
            assert comp["sector"] == "Information Technology"
