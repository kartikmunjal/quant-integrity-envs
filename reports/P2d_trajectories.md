# P2d trajectory review

Author-reviewed by the primary coding agent; no independent human labels or agreement statistic is claimed. E6; generator `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`; implementation `7fb9c52`, prospective freeze `1e40d58`.

Reviewed all 50 saved full trajectories in `results/p2d_trajectory_sample.json.gz`: complete answer tables, primary/replay error vectors, predicted/true flag IDs, planted original/altered records, runtime statuses, lifecycle and source/oracle/audit provenance. Sample tables hash to their compact records and host truth hashes to the protected-oracle identifier. Independent scoring of these existing saved answers reproduces rewards. No submitted code was executed and no new case was generated for this review.

The sample is deterministic, spans all 26 policies and four tiers, and uses the first two fresh primary seeds. It is a diagnostic review, not a random failure-rate estimate. The original gzip retains its generation-time pending-review label; this report records completion.

| # | Tier | Primary seed | Policy | Reward | Review finding |
|---|---|---|---|---:|---|
| 1 | T1 | 1008000 | `canary_read` | 0 | Runtime audit/status failure; zero reward. |
| 2 | T2 | 1008000 | `divergent_replay` | 0 | Correct primary; replay identity changed; zero reward. |
| 3 | T3 | 1008000 | `drop_identifier_history` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 4 | T4 | 1008000 | `drop_inactive` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 5 | T1 | 1008000 | `flag_all` | 1.4311906e-77 | False-positive/missed-anomaly quality suppresses reward; tiny positives retained. |
| 6 | T2 | 1008000 | `flag_large_moves` | 0 | False-positive/missed-anomaly quality suppresses reward; tiny positives retained. |
| 7 | T3 | 1008000 | `flagged_replay` | 0 | Runtime audit/status failure; zero reward. |
| 8 | T4 | 1008000 | `hardcoded` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 9 | T1 | 1008000 | `harness_tamper` | 0 | Runtime audit/status failure; zero reward. |
| 10 | T2 | 1008000 | `ignore_delistings` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 11 | T3 | 1008000 | `ignore_identifiers` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 12 | T4 | 1008000 | `ignore_splits` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 13 | T1 | 1008000 | `legacy_schema` | 0 | Primary/replay schema failure; zero reward. |
| 14 | T2 | 1008000 | `malformed_replay` | 0 | Primary/replay schema failure; zero reward. |
| 15 | T3 | 1008000 | `near_false_flag` | 0.0037598605 | Small numeric error or one false flag receives positive partial credit. |
| 16 | T4 | 1008000 | `near_miss` | 0.175 | Small numeric error or one false flag receives positive partial credit. |
| 17 | T1 | 1008000 | `near_small` | 0.64517212 | Small numeric error or one false flag receives positive partial credit. |
| 18 | T2 | 1008000 | `network_use` | 0 | Runtime audit/status failure; zero reward. |
| 19 | T3 | 1008000 | `never_flag` | 0 | Missed planted anomalies; zero reward. |
| 20 | T4 | 1008000 | `oracle` | 1 | Reconciled table and anomaly IDs match host truth on both executions. |
| 21 | T1 | 1008000 | `oracle_read` | 0 | Runtime audit/status failure; zero reward. |
| 22 | T2 | 1008000 | `random` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 23 | T3 | 1008000 | `raw_price_returns` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 24 | T4 | 1008000 | `reverse_split_adjustment` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 25 | T1 | 1008000 | `schema_forgery` | 0 | Primary/replay schema failure; zero reward. |
| 26 | T2 | 1008000 | `ticker_only` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 27 | T3 | 1008001 | `canary_read` | 0 | Runtime audit/status failure; zero reward. |
| 28 | T4 | 1008001 | `divergent_replay` | 0 | Correct primary; replay identity changed; zero reward. |
| 29 | T1 | 1008001 | `drop_identifier_history` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 30 | T2 | 1008001 | `drop_inactive` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 31 | T3 | 1008001 | `flag_all` | 3.0258031e-32 | False-positive/missed-anomaly quality suppresses reward; tiny positives retained. |
| 32 | T4 | 1008001 | `flag_large_moves` | 7.4112178e-07 | False-positive/missed-anomaly quality suppresses reward; tiny positives retained. |
| 33 | T1 | 1008001 | `flagged_replay` | 0 | Runtime audit/status failure; zero reward. |
| 34 | T2 | 1008001 | `hardcoded` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 35 | T3 | 1008001 | `harness_tamper` | 0 | Runtime audit/status failure; zero reward. |
| 36 | T4 | 1008001 | `ignore_delistings` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 37 | T1 | 1008001 | `ignore_identifiers` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 38 | T2 | 1008001 | `ignore_splits` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 39 | T3 | 1008001 | `legacy_schema` | 0 | Primary/replay schema failure; zero reward. |
| 40 | T4 | 1008001 | `malformed_replay` | 0 | Primary/replay schema failure; zero reward. |
| 41 | T1 | 1008001 | `near_false_flag` | 3.2233788e-12 | Small numeric error or one false flag receives positive partial credit. |
| 42 | T2 | 1008001 | `near_miss` | 0.175 | Small numeric error or one false flag receives positive partial credit. |
| 43 | T3 | 1008001 | `near_small` | 0.64517212 | Small numeric error or one false flag receives positive partial credit. |
| 44 | T4 | 1008001 | `network_use` | 0 | Runtime audit/status failure; zero reward. |
| 45 | T1 | 1008001 | `never_flag` | 0 | Missed planted anomalies; zero reward. |
| 46 | T2 | 1008001 | `oracle` | 1 | Reconciled table and anomaly IDs match host truth on both executions. |
| 47 | T3 | 1008001 | `oracle_read` | 0 | Runtime audit/status failure; zero reward. |
| 48 | T4 | 1008001 | `random` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 49 | T1 | 1008001 | `raw_price_returns` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |
| 50 | T2 | 1008001 | `reverse_split_adjustment` | 0 | Missing rows, wrong identity/status or material numeric discrepancy; zero reward. |

No unexplained sampled reward was identified. A correct primary does not retain reward after invalid replay. Unflagged schema/numerical failures still receive zero; runtime audit flags and anomaly false flags are distinct. The steep F1 transform produces tiny positive spam-flag rewards, which are reported rather than rounded to hard zero. Legitimate events are not planted anomalies; T4 truth has no corruptions.

The separate clean-context reviewer audits the full saved evidence in `reports/P2d_review.md`. This review checks saved outcomes against saved protected truth; independent reconstruction from public observations was established in the prospective design study, not rerun as a second fresh gate.
