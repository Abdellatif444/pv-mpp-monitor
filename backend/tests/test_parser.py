import pytest
from app.utils.parser import parse_text_samples


def test_parse_text_samples_basic():
    text = """
    V:20.2V I:0.10A P:2.1W
    V:1.7V I:17.24A P:28.8W
    """.strip()
    samples = parse_text_samples(text)
    assert len(samples) == 2
    assert samples[0]['V'] == 20.2
    assert samples[0]['I'] == 0.10
    assert samples[0]['P'] == pytest.approx(2.02, 0.2)  # either parsed 2.1 or computed 2.02


def test_parse_text_samples_without_power():
    text = "V:10V I:2A"
    samples = parse_text_samples(text)
    assert len(samples) == 1
    assert samples[0]['P'] == 20.0
