def calc_roe(net_income, equity):
    if equity is None or equity <= 0:
        return None
    return net_income / equity


def calc_de(debt, equity):
    if debt == 0:
        return 0.0
    if equity is None or equity <= 0:
        return None
    return debt / equity


def calc_icr(ebit, interest):
    if interest is None or interest <= 0:
        return None
    return ebit / interest


def check_de_flag(de, is_financial=False):
    if not is_financial and de is not None and de > 5:
        return True
    return False


def check_cagr_turnaround(old_val, new_val):
    if old_val < 0 and new_val > 0:
        return True
    return False


def check_cagr_decline(old_val, new_val):
    if old_val > 0 and new_val < 0:
        return True
    return False


def calc_cagr(start, end, years):
    if start <= 0 or end <= 0:
        return 0.0
    return (end / start) ** (1 / years) - 1


def check_opm_divergence(opm1, opm2):
    return abs(opm1 - opm2) > 0.1


def cfo_quality_score(cfo, net_income):
    if net_income == 0:
        return 0.0
    return cfo / net_income
