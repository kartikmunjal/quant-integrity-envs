# M0 packaging - STOP

M0 documentation packaging is complete. No new scientific experiment was run. The generator, E1, E5 and E6 are presented with their recorded validation, while mutation-engine/E2 implementation remains explicitly unvalidated. E2's partial first gate and the subsequent infrastructure correction/admission failure are below the validated numerical summary. Planned E3/E4, baselines and training are labelled planned. M1 is not claimed.

## Files and checks

| Requirement | Evidence | Result |
|---|---|---|
| Paper-style README in requested order | `README.md`, authored through `docs/README.template.md` | PASS |
| Every README table generated from existing result artifacts | `scripts/reproduce_table.py`, named `--table` renderers and `--check` | PASS |
| Numerical drift guard | 15 tests passed, zero failures/errors/skips; tests alter README numbers and source values and verify rejection | PASS |
| Correct reward definitions and stored sensitivity curves | Existing E1/E5 reward sources and revised E6 curve cross-checked by tests | PASS |
| Historical reports/results/logs/freezes and experiment code preserved | Empty Git diff for protected directories and configuration | PASS |
| M0 current target and claim boundaries | `docs/MILESTONES.md` | PASS |
| Resume draft | Exactly three source-generated bullets in `docs/resume_bullets.md`, numerical claims only from `results/` | PASS |
| No em dashes in M0-authored files | Checked before commit; historical files left unchanged | PASS |
| Release review, license, rename, visibility changes | None performed; release review belongs to owner | PASS |
| Repository inventory and large-file flags | `docs/M0_repo_inventory.json` | PASS |

The current packaging checks and file hashes are recorded in `docs/M0_packaging_checks.json`. Commands executed:

```bash
uv run python scripts/reproduce_table.py --write
uv run python scripts/reproduce_table.py --check
uv run pytest tests/test_readme_tables.py
```

These are document regeneration and software checks, not gate reruns. The source-backed resume statements distinguish historical numerical-runtime stress from corrected-runtime regression. No model result or unvalidated component is represented as completed.

## Interpretations and observations

Only README, documentation, the table script and its new tests were changed. The requested milestone document is an explicitly authorized documentation edit even though old freezes record its former hash. No historical freeze is updated or relabeled. STATE remains the last scientific phase status because the prompt limits edits to packaging files; the M0 target is recorded in the milestone document.

The old E2 status labels, including **failed and remains incomplete** and **partial gate observations, not a gate pass**, are retained. The outdated claim that its infrastructure fix was merely planned is replaced by the already recorded correction and failed stress prerequisite. This adds no new experiment or pass claim.

One important aggregation trap was found: the fresh generator artifact retains per-case flags from the original factor-share threshold. Those flags cannot describe the amended criterion. The generated table instead checks the stored per-case measurements against the recorded amended per-seed thresholds and verifies the count against the stored summary. The original failed screen remains separate. A regression test rejects the earlier incorrect aggregation. No historical case flag, result or threshold was changed.

Numerical policy tables use the recorded policy cells, each with the recorded common population; extra oracle coverage is identified separately. Worst wrong/cheater means are maxima across the frozen policy rosters, whose membership is checked against the existing policy generators. Near controls are shown separately. E6 uses the revised reward-sensitivity artifact rather than the retired earlier curve. Display rounding is documented; exact values stay in their source JSON.

The complete README is compared against its rendering, so manually changing a number in prose or a table fails the check. Formula coefficients, quality-band endpoints, retry allowance and sample counts are separately checked against configuration, recorded bands and the existing implementation. Template edits should be followed by `--write` and the tests. Source-result changes are not authorized by this packaging task.

No independent verifier-review session was started because this task adds no verifier or financial implementation. Historical independent-checker and AI-review provenance is retained, with no invented human labels or author reviews.

## Repository size

Snapshot method and timestamp are in `docs/M0_repo_inventory.json`. These are logical bytes, not allocated/deduplicated disk usage. Symlink targets were not traversed. The snapshot was taken after staging the primary M0 files and before adding inventory/closing-report files and the final commit, so it is a recorded point-in-time inventory.

- Tracked working files: **650,285,575 bytes** across **16,373 files**.
- Git directory: **99,839,171 bytes**.
- Full repository directory, including ignored raw evidence, environment and caches: **2,779,440,856 bytes**.
- Tracked files over **20,000,000 bytes**: **0**. No oversized tracked file is flagged. No history, cache or evidence was removed to reduce these figures.

| Largest tracked files at snapshot | Bytes |
|---|---:|
| `uv.lock` | 725,192 |
| `results/p2b2_rollouts/T1-oracle.json` | 653,661 |
| `results/p2b2_rollouts/T2-oracle.json` | 653,656 |
| `results/p2b2_rollouts/T4-oracle.json` | 653,650 |
| `results/p2b2_rollouts/T3-oracle.json` | 653,578 |
| `results/p3a_interrupted_review_packet/rows-0016.jsonl.gz` | 522,517 |
| `results/p3a_interrupted_review_packet/rows-0006.jsonl.gz` | 521,025 |
| `results/p3a_interrupted_review_packet/rows-0001.jsonl.gz` | 520,965 |
| `results/p3a_interrupted_review_packet/rows-0013.jsonl.gz` | 516,449 |
| `results/p3a_interrupted_review_packet/rows-0011.jsonl.gz` | 515,937 |

Historical Git blob metadata was also checked without changing history. Reachable blobs over 20,000,000 bytes: **0**. The largest reachable historical blob is `logs/p3a_runtime_design_tests_fixed.xml` at **6,358,089 bytes**. Details and object IDs are retained in the inventory. No oversized historical object was removed.

## Spend and completion

This packaging task made zero model/API calls, used no GPUs, and ran no scientific gate, model baseline, training or sealed evaluation. Experimental spend: API $0 and GPU $0. The software test suite recorded **3.191 seconds** in JUnit; its summary is in `docs/M0_packaging_checks.json`; no Docker workload was started by this task. Existing experimental compute remains reported in its historical artifacts, not charged again to M0.

The report, README, template, table renderer, tests, milestones, resume draft and inventory are committed and pushed as authorized. Only `P2B_PROMPT4.md` is deleted at completion; the owner's other prompt is preserved. The exact packaging commit hash is provided in the final response and Git history, rather than inserting an impossible self-referential hash here. Release review was skipped as instructed. STOP and await the owner; no next phase is started.
