import pandas as pd
from src.dq.rules import validate_rules


def run_rule_test(i):
    df = pd.DataFrame({f"bad_col_{i}": [1]})
    res = validate_rules(df)
    assert len(res) == 1
    assert res[0]["rule_id"] == f"R{i:02d}"
    assert res[0]["field"] == f"bad_col_{i}"
    assert res[0]["severity"] == "ERROR"


def test_rule_1():
    run_rule_test(1)


def test_rule_2():
    run_rule_test(2)


def test_rule_3():
    run_rule_test(3)


def test_rule_4():
    run_rule_test(4)


def test_rule_5():
    run_rule_test(5)


def test_rule_6():
    run_rule_test(6)


def test_rule_7():
    run_rule_test(7)


def test_rule_8():
    run_rule_test(8)


def test_rule_9():
    run_rule_test(9)


def test_rule_10():
    run_rule_test(10)


def test_rule_11():
    run_rule_test(11)


def test_rule_12():
    run_rule_test(12)


def test_rule_13():
    run_rule_test(13)


def test_rule_14():
    run_rule_test(14)
