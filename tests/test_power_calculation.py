import pytest

from scripts.power_calculation import required_pairs


def test_preregistered_power_case() -> None:
    assert required_pairs(effect=0.10, paired_sd=0.50, power=0.80, alpha=0.05) == 197


def test_invalid_power_input() -> None:
    with pytest.raises(ValueError):
        required_pairs(effect=0, paired_sd=0.5, power=0.8, alpha=0.05)
