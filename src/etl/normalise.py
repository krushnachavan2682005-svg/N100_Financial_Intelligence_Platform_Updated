def normalize_year(y):
    if y is None or str(y) == "nan":
        return None
    y = str(y).strip().lower()
    if (
        "mar 2024" in y
        or "fy24" in y
        or "2023-24" in y
        or "2024-03-31" in y
        or y == "2024"
    ):
        return 2024
    if (
        "mar 2023" in y
        or "fy23" in y
        or "2022-23" in y
        or "2023-03-31" in y
        or y == "2023"
    ):
        return 2023
    return None
