from decimal import Decimal
from pathlib import Path

import pytest

from scripts.budget_gate import read_spend, run_gate


def prereg(tmp_path: Path) -> Path:
    path = tmp_path / "prereg.yaml"
    path.write_text(
        "budgets:\n"
        "  api_usd_cap: 10\n"
        "  gpu_usd_cap: 20\n"
        "  total_usd_cap: 25\n"
        "  stop_and_report_at_fraction: 0.8\n",
        encoding="utf-8",
    )
    return path


def test_gate_records_allowed_spend(tmp_path: Path) -> None:
    log = tmp_path / "logs" / "spend.csv"
    decision = run_gate(prereg(tmp_path), log, "api", "1.25", "pilot")
    assert decision.accepted and not decision.stop_required
    assert read_spend(log)["api"] == Decimal("1.25")


def test_gate_stops_at_eighty_percent(tmp_path: Path) -> None:
    decision = run_gate(prereg(tmp_path), tmp_path / "spend.csv", "api", "8", "pilot")
    assert decision.accepted and decision.stop_required


def test_gate_refuses_at_cap_and_does_not_count_refusal(tmp_path: Path) -> None:
    log = tmp_path / "spend.csv"
    decision = run_gate(prereg(tmp_path), log, "api", "10", "full run")
    assert not decision.accepted
    assert read_spend(log)["api"] == 0


@pytest.mark.parametrize("amount", ["-1", "nan", "inf"])
def test_gate_rejects_invalid_amounts(tmp_path: Path, amount: str) -> None:
    with pytest.raises(ValueError):
        run_gate(prereg(tmp_path), tmp_path / "spend.csv", "api", amount, "invalid")
