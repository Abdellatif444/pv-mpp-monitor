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


def test_parse_csv_semicolon_keeps_timestamp():
    from app.utils.parser import parse_csv_bytes
    data = b"t;V;I\n2026-01-01T10:00:00;20.0;0.5\n2026-01-01T10:00:01;18.0;1.0\n"
    samples = parse_csv_bytes(data)
    assert len(samples) == 2
    assert samples[0]["t"] == "2026-01-01T10:00:00"
    assert samples[1]["P"] == 18.0
