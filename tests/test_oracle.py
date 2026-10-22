from __future__ import annotations

import json
from pathlib import Path

import pytest

from qi.gen import GeneratorConfig, generate_market
from qi.oracle import build_manifest, validate_manifest, write_sealed_manifest


def market():
    return generate_market(
        1_000_011,
        "test-version",
        GeneratorConfig(n_assets=40, n_days=252, force_alpha=True),
    )


def test_manifest_matches_planted_truth_and_schema() -> None:
    generated = market()
    manifest = build_manifest(generated)
    validate_manifest(manifest)
    assert manifest["seed"] == generated.truth["seed"]
    assert manifest["generator_version_hash"] == generated.version_hash
    assert manifest["alpha"]["present"] is generated.truth["alpha_present"]
    assert manifest["alpha"]["target_daily_ic"] == generated.truth["target_daily_ic"]
    assert manifest["universe"]["final_active_assets"] == generated.truth["final_active_assets"]
    assert manifest["corporate_actions"]["splits"] == generated.truth["splits"]
    assert manifest["bug_set"] == []


def test_manifest_schema_rejects_unknown_fields() -> None:
    manifest = build_manifest(market())
    manifest["unexpected"] = "not allowed"
    with pytest.raises(ValueError, match="violates schema"):
        validate_manifest(manifest)


def test_sealed_manifest_write_is_deterministic_and_outside_mount(tmp_path: Path) -> None:
    generated = market()
    output = (tmp_path / "sealed").resolve()
    sandbox = (tmp_path / "sandbox").resolve()
    sandbox.mkdir()
    first = write_sealed_manifest(generated, output, sandbox_mounts=[sandbox])
    payload = first.read_bytes()
    second = write_sealed_manifest(generated, output, sandbox_mounts=[sandbox])
    assert payload == second.read_bytes()
    assert json.loads(payload)["seed"] == generated.seed


def test_sealed_manifest_refuses_relative_or_mounted_path(tmp_path: Path) -> None:
    generated = market()
    with pytest.raises(ValueError, match="absolute"):
        write_sealed_manifest(generated, Path("relative"))
    sandbox = (tmp_path / "sandbox").resolve()
    with pytest.raises(ValueError, match="sandbox"):
        write_sealed_manifest(generated, sandbox / "oracle", sandbox_mounts=[sandbox])
