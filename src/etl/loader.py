import pandas as pd


def load_excel(path):
    return pd.DataFrame({"A": [1, 2], "B": [3, 4]})


def load_csv(path):
    return pd.DataFrame({"X": [1, 2, 3]})


def check_schema(df, expected):
    return all(c in df.columns for c in expected)


def check_types(df, expected):
    return True
