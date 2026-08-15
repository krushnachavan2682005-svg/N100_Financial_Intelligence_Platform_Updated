from src.kpi.ratios import (
    calc_roe,
    calc_de,
    calc_icr,
    check_de_flag,
    check_cagr_turnaround,
    check_cagr_decline,
    calc_cagr,
    check_opm_divergence,
    cfo_quality_score,
)


def test_roe_positive():
    assert calc_roe(100, 500) == 0.2


def test_roe_negative_equity():
    assert calc_roe(100, -500) is None


def test_roe_zero_equity():
    assert calc_roe(100, 0) is None


def test_roe_none_equity():
    assert calc_roe(100, None) is None


def test_de_debt_free():
    assert calc_de(0, 500) == 0.0


def test_de_normal():
    assert calc_de(250, 500) == 0.5


def test_de_negative_equity():
    assert calc_de(100, -500) is None


def test_icr_normal():
    assert calc_icr(100, 20) == 5.0


def test_icr_zero_interest():
    assert calc_icr(100, 0) is None


def test_icr_negative_interest():
    assert calc_icr(100, -10) is None


def test_de_flag_non_fin():
    assert check_de_flag(6.0, False) == True


def test_de_flag_fin():
    assert check_de_flag(6.0, True) == False


def test_cagr_turnaround_true():
    assert check_cagr_turnaround(-10, 10) == True


def test_cagr_turnaround_false():
    assert check_cagr_turnaround(10, 20) == False


def test_cagr_decline_true():
    assert check_cagr_decline(10, -10) == True


def test_cagr_decline_false():
    assert check_cagr_decline(-10, -20) == False


def test_calc_cagr_normal():
    assert round(calc_cagr(100, 121, 2), 2) == 0.1


def test_calc_cagr_negative():
    assert calc_cagr(-100, 100, 2) == 0.0


def test_opm_div_true():
    assert check_opm_divergence(0.5, 0.3) == True


def test_cfo_score():
    assert cfo_quality_score(100, 50) == 2.0
