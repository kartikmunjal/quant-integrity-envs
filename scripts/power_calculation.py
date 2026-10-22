#!/usr/bin/env python3
"""Conservative paired-episode sample-size calculation."""

from __future__ import annotations

import argparse
import math
from statistics import NormalDist


def required_pairs(effect: float, paired_sd: float, power: float, alpha: float) -> int:
    if effect <= 0 or paired_sd <= 0 or not 0 < power < 1 or not 0 < alpha < 1:
        raise ValueError("effect and SD must be positive; power and alpha must lie in (0, 1)")
    normal = NormalDist()
    z_alpha = normal.inv_cdf(1 - alpha / 2)
    z_power = normal.inv_cdf(power)
    return math.ceil(((z_alpha + z_power) * paired_sd / effect) ** 2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--effect", type=float, default=0.10)
    parser.add_argument("--paired-sd", type=float, default=0.50)
    parser.add_argument("--power", type=float, default=0.80)
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()
    print(required_pairs(args.effect, args.paired_sd, args.power, args.alpha))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
