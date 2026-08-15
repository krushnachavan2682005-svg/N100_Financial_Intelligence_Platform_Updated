import time
import pytest


def dummy_profile_load(ticker):
    # Mocking a dashboard component query function
    time.sleep(0.05)
    return True


@pytest.mark.parametrize("ticker", ["TCS", "RELIANCE", "HDFCBANK", "INFY", "ITC"])
def test_dashboard_profile_latency(ticker):
    start = time.time()
    dummy_profile_load(ticker)
    latency = time.time() - start
    assert latency < 3.0, f"{ticker} dashboard load took {latency}s"
