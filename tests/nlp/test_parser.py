from src.nlp.parser import parse_metric_text


def test_parse_metric_text_standard():
    text = "10 Years: 21.0%"
    results = parse_metric_text(text)
    assert len(results) == 1
    assert results[0] == (10, 21.0)


def test_parse_metric_text_multiple():
    text = "10 Years: 21.0%, 5 Years: 15.0%"
    results = parse_metric_text(text)
    assert len(results) == 2
    assert results[0] == (10, 21.0)
    assert results[1] == (5, 15.0)


def test_parse_metric_text_variations():
    # Test without colon
    assert parse_metric_text("5 Years 12.0%")[0] == (5, 12.0)
    # Test singular year
    assert parse_metric_text("1 Year: 5%")[0] == (1, 5.0)
    # Test case insensitivity
    assert parse_metric_text("3 yEaRs :  10.5%")[0] == (3, 10.5)


def test_parse_metric_text_invalid():
    assert parse_metric_text("Random text without numbers") == []
    assert parse_metric_text("10 Months: 20%") == []  # 'Months' doesn't match 'Years'
    assert parse_metric_text(None) == []


def test_parse_metric_text_edge_cases():
    text = "10 Years: 21.0%, invalid part, 3 Years: 10%"
    results = parse_metric_text(text)
    assert len(results) == 2
    assert results[0] == (10, 21.0)
    assert results[1] == (3, 10.0)
