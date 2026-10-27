# Current reward sensitivity (read-only P2d2 audit)

Environment E1/E5/E6; generator `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`; source commit `c2910b563ea14ab35dea421b2870f1695f889fa1`. All values come from actual unchanged score_pair calls on the recorded hand fixtures in `results/p2d2_reward_sensitivity.json`. No generated seed or new rollout is evaluated. Quality q is the current smoothstep value, not relative error itself.

Both executions have the indicated relative error. E1 perturbs both numbers; E5 perturbs both claims with exact canonical weights (Sharpe-only column shown separately); E6 perturbs prices with exact flags and identity. This is a controlled sensitivity slice, not all possible submissions.

| Relative error | q | E1 | E5 both claims | E5 Sharpe only | E6 numeric |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 1 | 1 | 1 | 1 |
| 0.0001 | 1 | 1 | 1 | 1 | 1 |
| 0.001 | 0.976709241 | 0.949517247 | 0.931742468 | 0.940629857 | 0.940629857 |
| 0.002575 | 0.84375 | 0.689666748 | 0.60067749 | 0.645172119 | 0.645172119 |
| 0.00505 | 0.5 | 0.225 | 0.125 | 0.175 | 0.175 |
| 0.007525 | 0.15625 | 0.0202941895 | 0.00381469727 | 0.0120544434 | 0.0120544434 |
| 0.01 | 0 | 0 | 0 | 1.2653243e-57 | 0 |
| 0.02 | 0 | 0 | 0 | 0 | 0 |

| Relative error on primary only; exact replay | E1 | E5 both claims | E6 numeric |
|---:|---:|---:|---:|
| 0 | 1 | 1 | 1 |
| 0.0001 | 1 | 1 | 1 |
| 0.001 | 0.976709241 | 0.956235772 | 0.963060262 |
| 0.002575 | 0.84375 | 0.725097656 | 0.764648438 |
| 0.00505 | 0.5 | 0.275 | 0.35 |
| 0.007525 | 0.15625 | 0.0375976563 | 0.0771484375 |
| 0.01 | 0 | 0 | 0 |
| 0.02 | 0 | 0 | 0 |

E6 exact reconciliation on both executions, no false flags:

| True corruptions n | Found k | F1 | Current reward |
|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 |
| 1 | 1 | 1 | 1 |
| 2 | 0 | 0 | 0 |
| 2 | 1 | 0.666666667 | 3.2233787751e-12 |
| 2 | 2 | 1 | 1 |
| 6 | 0 | 0 | 0 |
| 6 | 1 | 0.285714286 | 9.07395062917e-36 |
| 6 | 2 | 0.5 | 3.25260651796e-20 |
| 6 | 3 | 0.666666667 | 3.2233787751e-12 |
| 6 | 4 | 0.8 | 3.76825033418e-07 |
| 6 | 5 | 0.909090909 | 0.00138841786184 |
| 6 | 6 | 1 | 1 |

E6 finds every corruption, with exact reconciliation on both executions:

| True corruptions | False flags | F1 | Current reward |
|---:|---:|---:|---:|
| 1 | 0 | 1 | 1 |
| 1 | 1 | 0.666666667 | 3.2233787751e-12 |
| 1 | 2 | 0.5 | 3.25260651796e-20 |
| 2 | 0 | 1 | 1 |
| 2 | 1 | 0.8 | 3.76825033418e-07 |
| 2 | 2 | 0.666666667 | 3.2233787751e-12 |
| 6 | 0 | 1 | 1 |
| 6 | 1 | 0.923076923 | 0.00375986047589 |
| 6 | 2 | 0.857142857 | 3.13067589822e-05 |

E6 clean cases, exact reconciliation on both executions:

| False flags | Current reward |
|---:|---:|
| 0 | 1 |
| 1 | 0.00244140625 |
| 2 | 9.22021447348e-05 |
| 3 | 9.17911529541e-06 |
| 4 | 1.5376384e-06 |
| 5 | 3.57408265922e-07 |

Detection curves use F1=2k/(n+k+false_flags). For exact reconciliation and equal F1, current reward is 0.6*F1^64+0.4*F1^96. Clean reward is 0.6*(1+false_flags)^(-8)+0.4*(1+false_flags)^(-12). The desired round-2 thresholds are not tuning targets used in this stopped audit.

The k-of-n rows are current-code hand-fixture sensitivities, not distributions from new scripted-policy rollouts. Full current historical rollout distributions remain in `results/p2d_gate.json`; no original artifact was changed.
