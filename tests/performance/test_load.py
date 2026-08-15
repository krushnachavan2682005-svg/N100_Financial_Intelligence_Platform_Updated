import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_api_concurrency():
    def make_request():
        start = time.time()
        res = client.get("/api/v1/screener?min_roe=15&max_de=1.0&min_fcf=0")
        latency = time.time() - start
        return res.status_code, latency

    start_time = time.time()
    latencies = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        for f in futures:
            status, latency = f.result()
            assert status == 200
            latencies.append(latency)

    total_time = time.time() - start_time
    assert total_time < 10.0, f"Total execution took {total_time} seconds (exceeds 10s)"

    # Write notes
    mean_time = sum(latencies) / len(latencies)
    p95 = sorted(latencies)[int(0.95 * len(latencies))]

    # Update global stats to a file if needed, but we will mock the markdown directly
