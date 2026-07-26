import pytest

from src.etl.normaliser import normalize_year


@pytest.mark.parametrize(
    "input_value, expected",
    [
        (2023, 2023),
        (2023.0, 2023),
        ("2023", 2023),
        (" 2023 ", 2023),
        ("FY 2023", 2023),
        ("Mar 2023", 2023),
        ("2022-23", 2023),
        ("2022-2023", 2023),
        ("2022/23", 2023),
        ("", None),
        ("   ", None),
        (None, None),
        ("-", None),
        ("nan", None),
        ("abc", None),
        (1800, None),
        (2050, None),
        (2023.5, None),
        ("2021-23", None),
        (True, None),
    ],
)
def test_normalize_year(input_value, expected):
    assert normalize_year(input_value) == expected
