import pytest

from src.etl.normaliser import normalize_ticker


@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("RELIANCE", "RELIANCE"),
        ("reliance", "RELIANCE"),
        (" reliance ", "RELIANCE"),
        ("RELIANCE.NS", "RELIANCE"),
        ("reliance.ns", "RELIANCE"),
        ("TCS.BO", "TCS"),
        (" tcs.bo ", "TCS"),
        ("HDFCBANK", "HDFCBANK"),
        (" hdfcbank ", "HDFCBANK"),
        ("INFY", "INFY"),
        ("infy.ns", "INFY"),
        ("", None),
        ("   ", None),
        (None, None),
        ("-", None),
        ("nan", None),
    ],
)
def test_normalize_ticker(input_value, expected):
    assert normalize_ticker(input_value) == expected
