# P0 power calculation

## Target

The preregistered target is 80% power for a two-sided paired comparison detecting an absolute mean reward difference of 0.10 at alpha 0.05.

## Conservative assumption

Rewards are bounded, but episode-paired differences can still be heterogeneous. Before any result exists, this calculation assumes a paired-difference standard deviation of 0.50. This is deliberately conservative relative to strongly correlated model pairs while avoiding an unsupported correlation estimate.

Using the normal approximation for the paired mean,

`n = ceil(((z_(1-alpha/2) + z_power) * sigma_paired / effect)^2)`.

With `alpha=0.05`, `power=0.80`, `sigma_paired=0.50`, and `effect=0.10`, the required count is **197 paired episodes per cell**.

Reproduce with:

```sh
python scripts/power_calculation.py --effect 0.10 --paired-sd 0.50 --power 0.80 --alpha 0.05
```

## Freeze implication

The draft `prereg.yaml` specifies 100 sealed-test episodes per cell. Because 197 exceeds 100, P0 does not silently change the preregistration. The owner must decide before freeze whether to raise the value or explicitly accept lower conservative power. No sealed-test data or model result was used in this calculation.

The normal approximation is a planning calculation. Final inference remains the preregistered paired bootstrap with 2,000 replicates and 95% confidence intervals.
