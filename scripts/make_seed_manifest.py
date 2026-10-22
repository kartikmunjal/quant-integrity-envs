#!/usr/bin/env python3
"""Create a deterministic compact manifest for preregistered seed partitions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


def build_manifest(prereg_path: Path) -> dict[str, object]:
    config = yaml.safe_load(prereg_path.read_text(encoding="utf-8"))
    seeds = config["seeds"]
    partitions: dict[str, dict[str, int]] = {}
    for name in ("train", "dev", "sealed_test"):
        start, end = map(int, seeds[f"{name}_range"])
        if start > end:
            raise ValueError(f"invalid {name} range")
        partitions[name] = {"start": start, "end": end, "count": end - start + 1}
    ordered = sorted((value["start"], value["end"], key) for key, value in partitions.items())
    for previous, current in zip(ordered, ordered[1:]):
        if previous[1] >= current[0]:
            raise ValueError(f"overlapping seed partitions: {previous[2]} and {current[2]}")
    return {
        "schema_version": 1,
        "project": config["project"],
        "partitions": partitions,
        "episodes_per_cell": seeds["episodes_per_cell"],
    }


def canonical_bytes(manifest: dict[str, object]) -> bytes:
    return (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write_manifest(prereg_path: Path, output_path: Path) -> str:
    payload = canonical_bytes(build_manifest(prereg_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prereg", type=Path, default=Path("prereg.yaml"))
    parser.add_argument("--output", type=Path, default=Path("results/seed_manifest.json"))
    args = parser.parse_args()
    print(write_manifest(args.prereg, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
