#!/usr/bin/env python3
"""Record metered spend and enforce the preregistered API/GPU/total caps."""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Mapping

import yaml


FIELDNAMES = ("timestamp_utc", "category", "amount_usd", "description", "status")


@dataclass(frozen=True)
class GateDecision:
    accepted: bool
    stop_required: bool
    reason: str
    projected: Mapping[str, Decimal]


def _money(value: object) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("amounts and caps must be decimal numbers") from exc
    if not result.is_finite() or result < 0:
        raise ValueError("amounts and caps must be finite and non-negative")
    return result


def load_limits(prereg_path: Path) -> tuple[dict[str, Decimal], Decimal]:
    config = yaml.safe_load(prereg_path.read_text(encoding="utf-8"))
    budgets = config["budgets"]
    caps = {
        "api": _money(budgets["api_usd_cap"]),
        "gpu": _money(budgets["gpu_usd_cap"]),
        "total": _money(budgets["total_usd_cap"]),
    }
    return caps, _money(budgets["stop_and_report_at_fraction"])


def read_spend(log_path: Path) -> dict[str, Decimal]:
    totals = {"api": Decimal("0"), "gpu": Decimal("0")}
    if not log_path.exists():
        return totals
    with log_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("status") not in {"accepted", "stop"}:
                continue
            category = row.get("category")
            if category not in totals:
                raise ValueError("spend log contains an unknown category")
            totals[category] += _money(row["amount_usd"])
    return totals


def decide(
    category: str,
    amount: Decimal,
    totals: Mapping[str, Decimal],
    caps: Mapping[str, Decimal],
    stop_fraction: Decimal,
) -> GateDecision:
    if category not in {"api", "gpu"}:
        raise ValueError("category must be api or gpu")
    amount = _money(amount)
    projected = {
        "api": totals["api"] + (amount if category == "api" else 0),
        "gpu": totals["gpu"] + (amount if category == "gpu" else 0),
    }
    projected["total"] = projected["api"] + projected["gpu"]
    reached_cap = [name for name in (category, "total") if projected[name] >= caps[name]]
    if reached_cap:
        return GateDecision(False, True, "cap reached: " + ",".join(reached_cap), projected)
    reached_stop = [
        name for name in (category, "total") if projected[name] >= caps[name] * stop_fraction
    ]
    return GateDecision(True, bool(reached_stop), "80% stop threshold reached" if reached_stop else "ok", projected)


def append_record(
    log_path: Path, category: str, amount: Decimal, description: str, status: str
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not log_path.exists() or log_path.stat().st_size == 0
    with log_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        if needs_header:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "category": category,
                "amount_usd": format(amount, "f"),
                "description": description,
                "status": status,
            }
        )


def run_gate(
    prereg_path: Path, log_path: Path, category: str, amount: object, description: str
) -> GateDecision:
    amount_decimal = _money(amount)
    caps, stop_fraction = load_limits(prereg_path)
    decision = decide(category, amount_decimal, read_spend(log_path), caps, stop_fraction)
    status = "refused" if not decision.accepted else "stop" if decision.stop_required else "accepted"
    append_record(log_path, category, amount_decimal, description, status)
    return decision


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", required=True, choices=("api", "gpu"))
    parser.add_argument("--amount-usd", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--prereg", type=Path, default=Path("prereg.yaml"))
    parser.add_argument("--log", type=Path, default=Path("logs/spend.csv"))
    args = parser.parse_args()
    decision = run_gate(args.prereg, args.log, args.category, args.amount_usd, args.description)
    print("REFUSED" if not decision.accepted else "STOP" if decision.stop_required else "ALLOW")
    return 1 if not decision.accepted else 2 if decision.stop_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
