import hashlib
from pathlib import Path

import pytest

from scripts.make_seed_manifest import build_manifest, write_manifest


def config(tmp_path: Path, ranges: str = "") -> Path:
    path = tmp_path / "prereg.yaml"
    path.write_text(
        "project: test\nseeds:\n"
        + (ranges or "  train_range: [0, 9]\n  dev_range: [10, 19]\n  sealed_test_range: [20, 29]\n")
        + "  episodes_per_cell: {dev: 2, sealed_test: 3}\n",
        encoding="utf-8",
    )
    return path


def test_manifest_is_deterministic_and_hash_matches(tmp_path: Path) -> None:
    source = config(tmp_path)
    first, second = tmp_path / "one.json", tmp_path / "two.json"
    digest_one = write_manifest(source, first)
    digest_two = write_manifest(source, second)
    assert first.read_bytes() == second.read_bytes()
    assert digest_one == digest_two == hashlib.sha256(first.read_bytes()).hexdigest()
    assert build_manifest(source)["partitions"]["train"]["count"] == 10


def test_manifest_rejects_overlapping_partitions(tmp_path: Path) -> None:
    source = config(
        tmp_path,
        "  train_range: [0, 10]\n  dev_range: [10, 19]\n  sealed_test_range: [20, 29]\n",
    )
    with pytest.raises(ValueError, match="overlapping"):
        build_manifest(source)
