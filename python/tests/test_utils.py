from utils import normalize_country

def test_normalize_country():
    assert normalize_country("us") == "US"
    assert normalize_country("  fr  ") == "FR"
    assert normalize_country("gb") == "GB"