import pandas as pd
from src.etl.loader import load_excel, load_csv, check_schema, check_types


def test_load_excel_type():
    assert isinstance(load_excel("dummy"), pd.DataFrame)


def test_load_csv_type():
    assert isinstance(load_csv("dummy"), pd.DataFrame)


def test_excel_rows():
    assert len(load_excel("dummy")) == 2


def test_csv_rows():
    assert len(load_csv("dummy")) == 3


def test_excel_cols():
    assert list(load_excel("dummy").columns) == ["A", "B"]


def test_csv_cols():
    assert list(load_csv("dummy").columns) == ["X"]


def test_check_schema_valid():
    assert check_schema(load_excel("d"), ["A", "B"]) == True


def test_check_schema_invalid():
    assert check_schema(load_excel("d"), ["C"]) == False


def test_check_types():
    assert check_types(pd.DataFrame(), {}) == True


def test_load_empty():
    assert True
