# M1 packaging report

Outcome: PASS for M1 synthetic-validation documentation. Publication still requires the owner's full-history release review and explicit approval. No release-review pass is claimed.

Implementation commit: `6fb117da617334e7e9f3099363ff2dbbc592232f`. Scientific baseline: `824814c02007f0b396eefefd96c9c1b4d739032b`. The final report/checks commit follows separately in Git history.

## What changed

Updated README and its template to mark the mutation engine and E2 built and validated on the fresh P3a3 screened population. Added generated per-tier policy and separate non-held-out/planned-held-out family tables, task/tier/mutation descriptions, harmonic reward and soft clean-false-flag explanation. Retained the initial infrastructure-classification failure, fix, round-two heavy-tail admission failure and prospective construction-only screen limitation. Updated the overview, limitations, M1 milestone and three source-backed resume bullets.

Scientific provenance remains E2 generator `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`, runtime `fad402d113ca9e19f082ac45e3e0904edb128b9e672c351fe3a2d62eb699a827` and frozen implementation `0c83348ea8c5372b99e376befaad540d34a1c37c`. Existing numerical-taskset provenance stays attached to its original results. All new E2 tables read `results/p3a3-gate.json`; mutation counts/realizations in prose and resume read the retained mutation-design compact evidence. Input hashes and machine-readable checks are in `docs/M1_packaging_checks.json`.

## Packaging gates

| Criterion | Measured result | Outcome |
|---|---|---|
| Exact README/resume table check | PASS; 14 managed README tables, including the three new E2 renderers | PASS |
| Documentation tests | 31 passed; 0 failures, 0 errors, 0 skipped | PASS |
| E2 drift tests | Tier mean, family count, held-out summary and planned-population mutations rejected | PASS |
| Reward wording | Harmonic weights match preregistration; soft false-flag fixture matches recorded result | PASS |
| Historical reports/results/logs/freezes | Byte-unchanged from baseline | PASS |
| Scientific/frozen executable source, thresholds, rewards, generator | Byte-unchanged from baseline | PASS |
| No em dashes / license | None introduced | PASS |
| Milestone/release status | M1 synthetic-validation side reached; owner release review still required | PASS |

Tests: `uv run pytest tests/test_readme_tables.py --junitxml=.cache/m1_documentation_tests.xml`. Table check: `uv run python scripts/reproduce_table.py --check`. The tests and source-input digests above permit read-only verification without another gate or policy run. Tests exercise numeric formula fixtures, not a new development evaluation or sealed evaluation. No independent reviewer session was started for this packaging-only edit; no verifier was authored or changed.

## Interpretations

The prompt explicitly requests updating `docs/MILESTONES.md`; it also prohibits changes to frozen source. This document is in the historical P3a3 source inventory. I treated the specific milestone-document request as authorization for the documentation update, while preserving every frozen executable source and the historical freeze manifest. The old milestone bytes are still verified at the freeze's recorded implementation commit. The checks record the old/current milestone hashes. A current-working-tree freeze comparison will therefore see the intentional documentation drift; audit the historical freeze at its recorded commit, without rewriting the manifest or claiming the new documentation was used in that experiment.

The explicit packaging whitelist takes precedence over BRIEF's generic state/report convention: `STATE.md` and historical `reports/` remain unchanged, and this new report/check record lives under allowed `docs/`. MILESTONES records packaging completion. E3 was not started.

“Every table from P3a3” applies to the new E2 tables. Historical E1/E5/E6 and failed-E2 tables retain their own original evidence, never substituted with P3a3 values. Per-family counts overlap because interacting episodes may involve several families. Planned held-out family coverage here is synthetic verifier validation, not model-transfer measurement.

## Findings and limitations retained

The soft clean-false-flag control retains substantial partial credit; it is separate from the frozen cheater roster and oracle-clean false-positive gate. It is described plainly rather than hidden by a worst-cheater maximum. Construction screening rejected one of the thousand design seeds and excludes extreme-tail episodes. One script template, twelve mutations in three realizations, scripted-oracle solvability, predictable replay, local Docker only and the synthetic-to-real gap remain explicit. No model performance, training result or hosted-sandbox feasibility is claimed.

## Repository size

Snapshot taken during packaging before final metadata/commit, anchored to baseline `824814c02007f0b396eefefd96c9c1b4d739032b`. This is an inventory, not a cleanup or a change to historical evidence.

| Component | Bytes | MiB |
|---|---:|---:|
| Git storage (.git) | 131054389 | 124.98 |
| Tracked working files at snapshot | 681739318 | 650.16 |
| logs directory (tracked and local) | 255017009 | 243.20 |
| results directory (tracked and local) | 427653500 | 407.84 |
| Local artifacts directory | 2394620355 | 2283.69 |

Largest tracked file at snapshot: 725192 bytes. Component directory sizes overlap the tracked-file aggregate and must not be added to it. Package environment/cache sizes are not presented as Git repository size. Exact inventory and Git object statistics are retained in the checks JSON. No archive, history, cache or scientific evidence was deleted to reduce these numbers.

## Spend and compute

Packaging ran stored-artifact rendering and local documentation tests only. The recorded final documentation suite used 2.940000 local wall seconds in JUnit. Preliminary failing tests and earlier passing iterations remain in `.cache/`; their total CPU time and all editing/review overhead were not fully measured. No new experiment, model call or GPU job ran, so project API/GPU experiment spend is $0 and no paid-call ledger entry was created. No sealed-test metric was computed.

## STOP

M1 packaging is complete. Commit and push the authorized documentation and check record, delete only P2B_PROMPT8.md at completion, and wait for the owner. No next phase or publication is authorized by this report.
