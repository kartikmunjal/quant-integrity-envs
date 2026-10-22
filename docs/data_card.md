# Synthetic market generator data card

Generator version is the SHA-256 of the Python sources in `src/qi/gen/`. The frozen version is recorded in `prereg.yaml`; any later generator change requires another dated amendment. This generator uses synthetic data only and is not calibrated to any private or real market dataset.

## Intended use

The generator supplies deterministic episodes and sealed oracle truth for the six quantitative-integrity tasksets. It is designed to expose point-in-time, selection, cost, multiplicity, and data-reconciliation mistakes under controlled ground truth. It is not intended for forecasting real returns, estimating real transaction costs, or supporting investment decisions.

## Seed partitions and determinism

- Training: 0–999,999.
- Development: 1,000,000–1,009,999.
- Sealed test: 2,000,000–2,009,999.

The generator rejects seeds outside those ranges. A NumPy `Generator` is initialized from SHA-256 of `(seed, generator_version_hash)`. Canonical output serialization fixes key ordering, array order, shape, dtype endianness, and byte order. Identical seed, version, and configuration therefore produce identical bytes. P1 diagnostics use development seeds only; no sealed-test seed is generated or evaluated.

## Generating process

### Returns and factors

Three latent factor returns use Student-t innovations with 4 degrees of freedom. A two-state Markov volatility regime has persistence 0.98. A persistent log-volatility process multiplies the regime scale, creating both stochastic volatility and volatility clustering. Asset returns combine normally distributed factor loadings with Student-t idiosyncratic innovations. Per-asset idiosyncratic daily volatility is sampled uniformly from 1% to 3%.

### Planted alpha

The signal is a cross-sectionally standardized AR(1) process. Its decay is derived from a half-life sampled uniformly from 5 to 40 days. Non-null episodes sample a daily target information coefficient uniformly from 0.01 to 0.04; null episodes use zero. The next-day return receives a signal term scaled against that day's cross-sectional return dispersion. Oracle truth records presence, target IC, realized mean daily IC, and half-life.

### Fundamentals and point-in-time availability

Fundamental reports occur every 63 simulated days. Latent fundamentals follow a random walk. The initial report contains larger measurement noise, while a later restatement contains smaller noise. Initial availability lags are sampled from 1 to 60 days and recorded separately from period end. Restatements arrive another 10 to 120 days later. This preserves the distinction among economic period, first availability, and revised value.

### Universe and corporate actions

Annual delisting intensity is sampled from 1% to 5%, then converted to a horizon event probability. Delisted assets become inactive and subsequent returns are unavailable. Identifier changes and splits are generated independently, with exact asset, day, old/new identifier, and split factor recorded in oracle truth. The final active universe is recorded explicitly.

### Costs and capacity

Each asset has a synthetic bid-ask spread, average daily dollar volume, square-root-impact coefficient, and capacity estimate. Spreads and volumes are lognormal with broad textbook-style dispersion; impact coefficients and capacity fractions are bounded draws. These are stylized inputs for later cost-realism tasks, not empirical estimates.

## Oracle isolation

`src/qi/oracle.py` builds a JSON manifest conforming to `schemas/oracle_manifest.json`. The writer accepts only an absolute destination and rejects any destination overlapping a declared agent sandbox mount. It writes atomically. Callers are responsible for passing every sandbox mount and mounting only agent-visible generated artifacts, never the oracle directory.

## P1 diagnostic definitions and thresholds

Thresholds were fixed in tests before the generator implementation was measured:

| Property | Statistic | P1 threshold |
|---|---|---:|
| Fat tails | pooled return excess kurtosis | ≥ 1.00 |
| Volatility clustering | lag-1 autocorrelation of absolute equal-weighted return | ≥ 0.05 |
| Factor structure | share of covariance eigenvalues accounted for by largest three | ≥ 0.30 |
| Planted IC recovery | absolute difference between realized and target mean daily IC | ≤ 0.01 |

The reproducible P1 gate runs five fixed dev seeds with 240 assets and 700 days using `scripts/run_p1_gate.py`. Exact per-seed measurements and the generator hash are stored in `results/p1_diagnostics.json`.

## Known limitations

- The process is deliberately stylized and does not reproduce venue microstructure, order books, macroeconomic feedback, or real security-level event distributions.
- A single regime process creates common volatility dependence more cleanly than real markets.
- Corporate actions are limited to at most one identifier change and one split per asset in an episode.
- Fundamental restatements are always present in the generated report matrix and use simple additive noise.
- The planted signal is designed for measurable controlled IC, making it cleaner than most real signals.
- Passing these diagnostics establishes internal synthetic realism only. It is not evidence of external validity or live profitability.

## Reproduction

```sh
uv run python scripts/run_p1_gate.py
uv run pytest
```
