# Revised E6 reward sensitivity

Frozen implementation `09214c7`; generator `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`. Exact fixture inputs are specified here: one active row with price/adjusted_price100, return0.1 and stable identity; n true anomaly IDs, k retained true IDs and the specified extra false IDs. Raw numeric results and reward-file hash are in `results/p2d2_revision_sensitivity.json`. No generated seeds or new rollouts were used.

The prior E1/E5 sensitivity tables remain unchanged documentation. This table concerns revised E6 only. Both executions have the same error/flags; equal primary and replay quality is no longer multiplied.

| Relative price error | U | Paired reward | Primary error, exact replay |
|---:|---:|---:|---:|
| 0 | 1 | 1 | 1 |
| 0.0001 | 1 | 1 | 1 |
| 0.001 | 0.976709241 | 0.963060262 | 0.963060262 |
| 0.002575 | 0.84375 | 0.764648438 | 0.764648438 |
| 0.00505 | 0.5 | 0.35 | 0.35 |
| 0.007525 | 0.15625 | 0.0771484375 | 0.0771484375 |
| 0.01 | 0 | 0 | 0 |
| 0.02 | 0 | 0 | 0 |

Exact reconciliation, no false flags:

| Actual corruptions n | Found k | F1 | Reward |
|---:|---:|---:|---:|
| 0 | 0 | 1 | 1 |
| 1 | 0 | 0 | 0 |
| 1 | 1 | 1 | 1 |
| 2 | 0 | 0 | 0 |
| 2 | 1 | 0.666666667 | 0.296296296 |
| 2 | 2 | 1 | 1 |
| 6 | 0 | 0 | 0 |
| 6 | 1 | 0.285714286 | 0.0233236152 |
| 6 | 2 | 0.5 | 0.125 |
| 6 | 3 | 0.666666667 | 0.296296296 |
| 6 | 4 | 0.8 | 0.512 |
| 6 | 5 | 0.909090909 | 0.751314801 |
| 6 | 6 | 1 | 1 |

Exact reconciliation, all true corruptions found:

| n | False flags | F1 | Reward |
|---:|---:|---:|---:|
| 0 | 0 | 1 | 1 |
| 0 | 1 | 0 | 0.125 |
| 0 | 2 | 0 | 0.037037037 |
| 0 | 3 | 0 | 0.015625 |
| 1 | 0 | 1 | 1 |
| 1 | 1 | 0.666666667 | 0.296296296 |
| 1 | 2 | 0.5 | 0.125 |
| 1 | 3 | 0.4 | 0.064 |
| 2 | 0 | 1 | 1 |
| 2 | 1 | 0.8 | 0.512 |
| 2 | 2 | 0.666666667 | 0.296296296 |
| 2 | 3 | 0.571428571 | 0.186588921 |
| 6 | 0 | 1 | 1 |
| 6 | 1 | 0.923076923 | 0.786527082 |
| 6 | 2 | 0.857142857 | 0.629737609 |
| 6 | 3 | 0.8 | 0.512 |

These are formula sensitivities, not fresh gate distributions. Full fresh k-of-n and near-policy distributions are reported separately in the phase report and gate JSON.
