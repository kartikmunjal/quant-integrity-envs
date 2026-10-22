from scripts.run_p1_gate import DEV_SEEDS


def test_p1_gate_uses_dev_seeds_only() -> None:
    assert DEV_SEEDS == tuple(range(1_000_000, 1_000_005))
