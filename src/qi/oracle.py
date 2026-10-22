"""Sealed oracle-manifest construction and isolated persistence."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

import jsonschema

from qi.gen.model import MarketData


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "oracle_manifest.json"


def build_manifest(market: MarketData) -> dict[str, Any]:
    truth = market.truth
    return {
        "schema_version": 1,
        "seed": market.seed,
        "partition": truth["partition"],
        "generator_version_hash": market.version_hash,
        "alpha": {
            "present": truth["alpha_present"],
            "target_daily_ic": truth["target_daily_ic"],
            "realized_daily_ic": truth["realized_daily_ic"],
            "halflife_days": truth["alpha_halflife_days"],
        },
        "universe": {
            "final_active_assets": truth["final_active_assets"],
            "delisting_days": truth["delisting_days"],
        },
        "corporate_actions": {
            "identifier_changes": truth["identifier_changes"],
            "splits": truth["splits"],
        },
        "fundamentals": {
            "report_count": int(market.fundamental_initial.shape[0]),
            "availability_lag_min": int((market.fundamental_available_day - market.fundamental_period_end[:, None]).min()),
            "availability_lag_max": int((market.fundamental_available_day - market.fundamental_period_end[:, None]).max()),
            "restatement_count": int(market.fundamental_restated.size),
        },
        "cost_model": {
            "spread_bps": market.spread_bps.tolist(),
            "adv_usd": market.adv_usd.tolist(),
            "impact_coefficient": market.impact_coefficient.tolist(),
            "capacity_usd": market.capacity_usd.tolist(),
        },
        "bug_set": truth["bug_set"],
        "bug_locations": truth["bug_locations"],
        "correct_answers": truth["correct_answers"],
    }


def validate_manifest(manifest: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    try:
        jsonschema.Draft202012Validator(schema).validate(manifest)
    except jsonschema.ValidationError as exc:
        raise ValueError(f"oracle manifest violates schema at {list(exc.path)}") from exc


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def write_sealed_manifest(
    market: MarketData,
    output_directory: Path,
    *,
    sandbox_mounts: Iterable[Path] = (),
) -> Path:
    if not output_directory.is_absolute():
        raise ValueError("sealed output directory must be absolute")
    destination = output_directory.resolve()
    mounts = [path.resolve() for path in sandbox_mounts]
    if any(_is_within(destination, mount) or _is_within(mount, destination) for mount in mounts):
        raise ValueError("sealed output directory must be outside every sandbox mount")
    destination.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(market)
    validate_manifest(manifest)
    payload = (json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    target = destination / f"seed-{market.seed}.json"
    descriptor, temporary = tempfile.mkstemp(prefix=".oracle-", dir=destination)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target
