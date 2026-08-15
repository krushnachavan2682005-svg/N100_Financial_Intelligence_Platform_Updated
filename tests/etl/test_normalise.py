from src.etl.normalise import normalize_year


def test_norm_mar_2024():
    assert normalize_year("Mar 2024") == 2024


def test_norm_fy24():
    assert normalize_year("FY24") == 2024


def test_norm_2023_24():
    assert normalize_year("2023-24") == 2024


def test_norm_2024_exact():
    assert normalize_year("2024") == 2024


def test_norm_2024_date():
    assert normalize_year("2024-03-31") == 2024


def test_norm_mar_2023():
    assert normalize_year("Mar 2023") == 2023


def test_norm_fy23():
    assert normalize_year("FY23") == 2023


def test_norm_2022_23():
    assert normalize_year("2022-23") == 2023


def test_norm_2023_exact():
    assert normalize_year("2023") == 2023


def test_norm_2023_date():
    assert normalize_year("2023-03-31") == 2023


def test_norm_none():
    assert normalize_year(None) is None


def test_norm_nan():
    assert normalize_year("nan") is None


def test_norm_invalid():
    assert normalize_year("invalid") is None


def test_norm_spaces():
    assert normalize_year("  FY24  ") == 2024


def test_norm_caps():
    assert normalize_year("MAR 2024") == 2024


def test_norm_leap():
    assert normalize_year("2024-02-29") is None  # unsupported mock


def test_norm_fy_caps():
    assert normalize_year("fy24") == 2024


def test_norm_24_exact():
    assert normalize_year("2024 ") == 2024


def test_norm_23_exact():
    assert normalize_year(" 2023") == 2023


def test_norm_mar_23():
    assert normalize_year("mar 2023") == 2023
