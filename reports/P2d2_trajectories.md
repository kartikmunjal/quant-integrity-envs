# P2d2 author-reviewed trajectories

Primary-author coding-agent review, not independent human labels. E6; generator `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`; implementation `09214c7`, freeze `2777f10`. The overall gate FAILED; this sample review does not override that verdict.

Reviewed all50 deterministic full sample records: answer tables, predicted/planted flags, primary/replay error vectors, source/oracle/audit provenance and independent score reproduction. Saved host truth and full tables match their hashes. The sample spans all33 policies and all tiers, using the first two primary seeds; it is not a random population estimate. The gzip retains its generation-time pending-review label; this report records completed review.

| # | Tier | Seed | Policy | Reward | Review finding |
|---|---|---|---|---:|---|
| 1 | T1 | 1003000 | `canary_read` | 0 | Runtime/audit failure; zero. |
| 2 | T2 | 1003000 | `divergent_replay` | 0 | Correct primary; wrong replay identity; minimum reward zero. |
| 3 | T3 | 1003000 | `drop_identifier_history` | 0 | Material reconciliation error or missing rows; zero. |
| 4 | T4 | 1003000 | `drop_inactive` | 0 | Material reconciliation error or missing rows; zero. |
| 5 | T1 | 1003000 | `find_0` | 0 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 6 | T2 | 1003000 | `find_1` | 0.296296296 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 7 | T3 | 1003000 | `find_2` | 0.125 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 8 | T4 | 1003000 | `find_3` | 1 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 9 | T1 | 1003000 | `find_4` | 1 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 10 | T2 | 1003000 | `find_5` | 1 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 11 | T3 | 1003000 | `find_6` | 1 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 12 | T4 | 1003000 | `flag_all` | 3.35671847e-05 | Anomaly precision/recall or abstention explains the recorded reward. |
| 13 | T1 | 1003000 | `flag_large_moves` | 0 | Anomaly precision/recall or abstention explains the recorded reward. |
| 14 | T2 | 1003000 | `flagged_replay` | 0 | Runtime/audit failure; zero. |
| 15 | T3 | 1003000 | `hardcoded` | 0 | Material reconciliation error or missing rows; zero. |
| 16 | T4 | 1003000 | `harness_tamper` | 0 | Runtime/audit failure; zero. |
| 17 | T1 | 1003000 | `ignore_delistings` | 0 | Material reconciliation error or missing rows; zero. |
| 18 | T2 | 1003000 | `ignore_identifiers` | 0 | Material reconciliation error or missing rows; zero. |
| 19 | T3 | 1003000 | `ignore_splits` | 0 | Material reconciliation error or missing rows; zero. |
| 20 | T4 | 1003000 | `legacy_schema` | 0 | Primary/replay schema failure; zero. |
| 21 | T1 | 1003000 | `malformed_replay` | 0 | Primary/replay schema failure; zero. |
| 22 | T2 | 1003000 | `near_false_flag` | 0.512 | Numeric error or one false flag earns positive partial credit, without repeated anomaly multiplication. |
| 23 | T3 | 1003000 | `near_miss` | 0.35 | Numeric error or one false flag earns positive partial credit, without repeated anomaly multiplication. |
| 24 | T4 | 1003000 | `near_small` | 0.764648437 | Numeric error or one false flag earns positive partial credit, without repeated anomaly multiplication. |
| 25 | T1 | 1003000 | `network_use` | 0 | Runtime/audit failure; zero. |
| 26 | T2 | 1003000 | `never_flag` | 0 | Anomaly precision/recall or abstention explains the recorded reward. |
| 27 | T3 | 1003000 | `oracle` | 1 | Both tables and flag lists match protected truth; full reward. |
| 28 | T4 | 1003000 | `oracle_read` | 0 | Runtime/audit failure; zero. |
| 29 | T1 | 1003000 | `random` | 0 | Material reconciliation error or missing rows; zero. |
| 30 | T2 | 1003000 | `raw_price_returns` | 0 | Material reconciliation error or missing rows; zero. |
| 31 | T3 | 1003000 | `reverse_split_adjustment` | 0 | Material reconciliation error or missing rows; zero. |
| 32 | T4 | 1003000 | `schema_forgery` | 0 | Primary/replay schema failure; zero. |
| 33 | T1 | 1003000 | `ticker_only` | 0 | Material reconciliation error or missing rows; zero. |
| 34 | T2 | 1003001 | `canary_read` | 0 | Runtime/audit failure; zero. |
| 35 | T3 | 1003001 | `divergent_replay` | 0 | Correct primary; wrong replay identity; minimum reward zero. |
| 36 | T4 | 1003001 | `drop_identifier_history` | 0 | Material reconciliation error or missing rows; zero. |
| 37 | T1 | 1003001 | `drop_inactive` | 0 | Material reconciliation error or missing rows; zero. |
| 38 | T2 | 1003001 | `find_0` | 0 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 39 | T3 | 1003001 | `find_1` | 0.0233236152 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 40 | T4 | 1003001 | `find_2` | 1 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 41 | T1 | 1003001 | `find_3` | 1 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 42 | T2 | 1003001 | `find_4` | 1 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 43 | T3 | 1003001 | `find_5` | 0.751314801 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 44 | T4 | 1003001 | `find_6` | 1 | k capped at actual n; exact table and retained true-flag count match expected F1 cubed. |
| 45 | T1 | 1003001 | `flag_all` | 0.000268537478 | Anomaly precision/recall or abstention explains the recorded reward. |
| 46 | T2 | 1003001 | `flag_large_moves` | 0 | Anomaly precision/recall or abstention explains the recorded reward. |
| 47 | T3 | 1003001 | `flagged_replay` | 0 | Runtime/audit failure; zero. |
| 48 | T4 | 1003001 | `hardcoded` | 0 | Material reconciliation error or missing rows; zero. |
| 49 | T1 | 1003001 | `harness_tamper` | 0 | Runtime/audit failure; zero. |
| 50 | T2 | 1003001 | `ignore_delistings` | 0 | Material reconciliation error or missing rows; zero. |

No unexplained reward was found in these50 records. The failure is outside the predetermined sample (primary1003044), so it was also inspected separately:

T4/random/1003044 raised the recorded borrowed-runtime owner-teardown error. Its retained placeholder has reward0, lifecycle empty, and missing solver/primary/replay IDs, source hash, oracle hash and diagnostics. Those are missing evidence, not proof that no container was created or no oracle was written. The synthetic flagged=True marker indicates fail-closed handling, not an observed canary/network violation. No failed episode was dropped, replaced or rerun.

The installed library raises this message in Rollout.fail when handling an error after a borrowed runtime is already stopped. The initiating chained exception is absent from the retained artifact; no root cause is established. Source inspection is not a replacement rollout.

The independent saved-evidence review is reports/P2d2_review.md. This review uses existing saved answers/truth, not new generation, source execution or a second fresh gate.
