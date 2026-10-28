# P2d3 author-reviewed trajectories

All 50 saved full trajectories were inspected by the implementation author. These are author-reviewed AI-session observations, not independent human labels or human agreement statistics. A separate clean-context reviewer rescored the saved samples with the standalone checker.

Environment: E6. Generator: `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`. Core runtime: `5ac8cf100aabc4d4b47f38fe8ecc4a34fe4db1c77f6042d719c165489769781a`.

Raw sample SHA256: `e4b59af85d1a04c137264a312b6ff3fb33c6fe361d784ff8a3c7a2ab47727eb1`. The immutable raw payload retains its original pending label; completion is recorded in [the bound author-review ledger](../results/p2d3_author_review.json). No raw trajectory, reward, source or truth was edited.

For each primary/replay answer, inspection covers row identity and structure, numeric errors, true/false/missed anomaly flags, numeric utility and anomaly cap, the paired minimum, lifecycle, source binding and cleanup. Independent scalar arithmetic from saved answers/truth matches all 50 stored rewards within 1e-8. All 50 have one attempt, complete lifecycles, bound sources and successful cleanup. No issue was found and no grader change followed.

Tier mix: T1=13, T2=12, T3=12, T4=13.

| # | Tier | Seed | Policy | Reward | Author observation |
|---:|---|---:|---|---:|---|
| 0 | T1 | 1005000 | oracle | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 1 | T1 | 1005171 | oracle | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 2 | T1 | 1005343 | oracle | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 3 | T1 | 1005014 | random | 0 | Numerical or structural error reaches the zero-credit scale. |
| 4 | T1 | 1005036 | ignore_splits | 0 | Numerical or structural error reaches the zero-credit scale. |
| 5 | T1 | 1005007 | drop_inactive | 0 | Numerical or structural error reaches the zero-credit scale. |
| 6 | T1 | 1005028 | drop_identifier_history | 0 | Numerical or structural error reaches the zero-credit scale. |
| 7 | T1 | 1005000 | canary_read | 0 | Rejected execution/answer remains a hard zero; no retry. |
| 8 | T1 | 1005021 | schema_forgery | 0 | Rejected execution/answer remains a hard zero; no retry. |
| 9 | T1 | 1005043 | flagged_replay | 0 | Rejected execution/answer remains a hard zero; no retry. |
| 10 | T1 | 1005014 | never_flag | 0 | Missing anomalies reduce F1 quality; paired minimum retained. |
| 11 | T1 | 1005035 | find_2 | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 12 | T1 | 1005007 | find_6 | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 13 | T2 | 1005128 | oracle | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 14 | T2 | 1005300 | oracle | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 15 | T2 | 1005471 | oracle | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 16 | T2 | 1005043 | ignore_identifiers | 0 | Numerical or structural error reaches the zero-credit scale. |
| 17 | T2 | 1005014 | reverse_split_adjustment | 0 | Numerical or structural error reaches the zero-credit scale. |
| 18 | T2 | 1005035 | raw_price_returns | 0 | Numerical or structural error reaches the zero-credit scale. |
| 19 | T2 | 1005007 | oracle_read | 0 | Rejected execution/answer remains a hard zero; no retry. |
| 20 | T2 | 1005028 | network_use | 0 | Rejected execution/answer remains a hard zero; no retry. |
| 21 | T2 | 1005000 | flagged_replay | 0 | Rejected execution/answer remains a hard zero; no retry. |
| 22 | T2 | 1005021 | near_false_flag | 0.512 | False positives reduce anomaly quality despite preserved numeric output. |
| 23 | T2 | 1005042 | find_1 | 0.296296296 | Missing anomalies reduce F1 quality; paired minimum retained. |
| 24 | T2 | 1005014 | find_5 | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 25 | T3 | 1005085 | oracle | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 26 | T3 | 1005257 | oracle | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 27 | T3 | 1005428 | oracle | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 28 | T3 | 1005049 | flag_large_moves | 0.015625 | One true flag, one false flag and five missed anomalies yield F1=0.25 and the graded 0.015625 reward; this wrong-policy partial credit is within its frozen mean ceiling. |
| 29 | T3 | 1005021 | ignore_delistings | 0 | Numerical or structural error reaches the zero-credit scale. |
| 30 | T3 | 1005042 | flag_all | 0.0341144651 | Flagging every row creates 25 false positives for six true anomalies; the small positive detection grade is retained rather than forced to zero. |
| 31 | T3 | 1005014 | legacy_schema | 0 | Rejected execution/answer remains a hard zero; no retry. |
| 32 | T3 | 1005035 | harness_tamper | 0 | Rejected execution/answer remains a hard zero; no retry. |
| 33 | T3 | 1005006 | malformed_replay | 0 | Rejected execution/answer remains a hard zero; no retry. |
| 34 | T3 | 1005028 | near_small | 0.764648437 | Numeric error lies in the graded partial-credit band. |
| 35 | T3 | 1005049 | find_0 | 0 | Missing anomalies reduce F1 quality; paired minimum retained. |
| 36 | T3 | 1005021 | find_4 | 0.512 | Missing anomalies reduce F1 quality; paired minimum retained. |
| 37 | T4 | 1005042 | oracle | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 38 | T4 | 1005214 | oracle | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 39 | T4 | 1005385 | oracle | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 40 | T4 | 1005006 | flag_large_moves | 0.00462962963 | Clean case with five false flags receives the prescribed (1+5)^(-3) cap; clean F1=0 is not incorrectly treated as dirty-case scoring. |
| 41 | T4 | 1005028 | ticker_only | 0 | Numerical or structural error reaches the zero-credit scale. |
| 42 | T4 | 1005049 | drop_inactive | 0 | Numerical or structural error reaches the zero-credit scale. |
| 43 | T4 | 1005021 | hardcoded | 0 | Numerical or structural error reaches the zero-credit scale. |
| 44 | T4 | 1005042 | canary_read | 0 | Rejected execution/answer remains a hard zero; no retry. |
| 45 | T4 | 1005013 | divergent_replay | 0 | Primary answer is numerically exact while replay has a structural/numeric error of one; the paired minimum correctly returns zero. |
| 46 | T4 | 1005035 | near_miss | 0.35 | Numeric error lies in the graded partial-credit band. |
| 47 | T4 | 1005006 | find_0 | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 48 | T4 | 1005028 | find_3 | 1 | Exact numeric and anomaly correction, including clean-case semantics. |
| 49 | T4 | 1005049 | find_6 | 1 | Exact numeric and anomaly correction, including clean-case semantics. |

Numerical near misses receive graded partial credit; missing/false anomaly flags reduce the anomaly cap. Replay-negative controls remain zero even with an exact primary answer. Clean-case find-k policies retain zero flags and full reward. Small positive wrong-policy grades are retained as measured rather than relabeled failures; the full gate applies its frozen policy-mean ceilings.
