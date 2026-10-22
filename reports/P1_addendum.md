# Phase P1 diagnostic addendum report

Date: 2026-10-21 (America/Denver)

Status: failed gate, awaiting owner decision. P2 was not started.

## What was built

- `6588287` — deterministic 200-dev-seed diagnostic runner, tests, and recorded results.
- `scripts/run_p1_addendum.py` samples dimensions independently and deterministically from each
  seed using SHA-256, with `n_assets` in the frozen inclusive range [200, 1000] and `n_days` in
  [500, 1500].
- The generator, diagnostic thresholds, and frozen preregistration were not changed.

## Gate results

All measurements are reproduced by `results/p1_addendum_diagnostics.json`, environment
`shared-generator`, generator version
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`, using dev seeds
1,000,000 through 1,000,199 only.

| Stylized-fact check | Passing seeds | Pass rate | Frozen threshold | Result |
|---|---:|---:|---:|---|
| Excess kurtosis | 200/200 | 100.0% | >= 1.00 | PASS |
| Lag-1 absolute-return autocorrelation | 200/200 | 100.0% | >= 0.05 | PASS |
| Top-three eigenvalue share | 167/200 | 83.5% | >= 0.30 | FAIL |
| IC recovery absolute error | 200/200 | 100.0% | <= 0.01 | PASS |
| All four checks per seed | 167/200 | 83.5% | all | FAIL |

| Requested distribution | Minimum | Median | Maximum |
|---|---:|---:|---:|
| Excess kurtosis | 9.233651 | 19.742712 | 291.927503 |
| Top-three eigenvalue share | 0.196094 | 0.376832 | 0.600012 |
| IC recovery absolute error | 0.000002 | 0.001091 | 0.004805 |

The full local test suite passed: 35/35 tests. The addendum process exited nonzero because the
all-checks pass rate was not 100 percent. Per the owner's instruction, work stopped and none of
P2's tests, environments, verifiers, checkers, or gates were started.

## Interpretations

1. "200 dev seeds" means the first 200 seeds in the frozen dev partition, 1,000,000–1,000,199.
2. "Dimensions sampled from the frozen ranges" means inclusive uniform integer mappings into
   each frozen range from a domain-separated SHA-256 digest of the seed. Sampling is independent
   of the generator RNG and reproducible.
3. Alpha was forced present, matching the original P1 diagnostic gate, because IC recovery is the
   requested diagnostic and is otherwise not meaningful on null episodes.
4. A check passes at equality with its existing threshold. No threshold was changed.

## Surprises

- Factor structure failed for 33 of 200 seeds despite the original five-seed fixed-dimension gate
  passing. The lowest observed share was 0.196094. This is reported without changing the
  generator, diagnostic, threshold, seeds, or sampled dimensions.
- Excess kurtosis reached 291.927503 on one seed; the value is retained as generated.
- No independent reviewer session was used because the gate failed before P2 verifier work began.

## Spend and compute

- `logs/spend.csv`: absent; no paid call occurred.
- API spend: USD 0.00. GPU spend: USD 0.00. Total spend: USD 0.00.
- Model calls: 0. Sealed-test seeds: 0. GPU use: 0.
- Addendum: 200 generated dev cases; recorded wall time 18.951345 seconds.

