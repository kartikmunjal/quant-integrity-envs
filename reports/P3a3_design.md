# P3a round 3 prospective design

Authorization: P2B_PROMPT7.md. This document is written before round-three construction measurements, code changes, Docker or policy runs. Preserve all historical evidence. E2 generator hash: eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921. No generator, mutation, financial reward, threshold, tier or weight changes.

## Construction measurement and screen

Measure every seed in design 1000000..1000999, primary reserved 1003000..1003999 and replay reserved 1004000..1004999 using construction only. Record all exhausted 32-candidate seeds, errors and rates in results/p3a3_screen.json. The existing admitted_data algorithm and its fallback remain unchanged. Check make_case for all four tiers as well, so a construction-only interaction failure cannot enter the population. Unexpected errors stop screening rather than count as routine exclusions.

Screen predicate: admitted_data succeeds and make_case succeeds for every tier. It depends only on seed, frozen construction code and generator, never on a policy, reward or Docker execution. Sort seeds ascending. Stress uses screened design seeds with the unchanged 5000-row mixed-policy schedule at concurrency 8 then 12. Primary population is the first 500 admissible seeds from 1003000, strictly below 1004000. Replay population is the first 1000 admissible seeds starting at 1004000 within the dev range through 1009999. Stop if insufficient or overlapping. Fully measure the originally reserved replay block; extend construction screening only as needed to obtain its population. Design replay uses screened design seeds; fresh gate replay uses the committed replay list, indexed by the unchanged SHA256 seed/tier/patch formula modulo list length. Commit exact admissible/rejected lists, cause counts and source hashes before any policy runs or freeze.

Limitation: extreme-tail episodes that cannot satisfy the unchanged price-return construction domain are excluded. Results describe the screened population, not all generator draws. Prior scripted gate and stress results have been seen; no model baseline or sealed-test result has been seen.

## Validation and execution

Write deterministic and policy-independent screen tests before implementation. Retain rejected seeds without reward-based filtering. Use new p3a3 evidence names, never overwrite prior artifacts. Stress requires 5000/5000 complete and infrastructure-healthy rows per concurrency and retries <=0.5%, with fresh containers and existing bounded archives. If either run fails for any reason, stop and report, without freeze or gate.

If both pass, retain the round-two 8200-row schedule and all numerical/anti-cheating criteria, fresh shallow T2/T3 detector measurement, independent scalar checker, 50 prospectively selected author-reviewed trajectories, independent clean-context review, source/design/image freeze and a new exclusive consumed marker. Keep the round-two exact E1/E5/E6 regressions as prerequisites; repeat if shared runtime changes. No shared runtime or financial change is planned. No models, API spend, GPU or sealed evaluation. Record wall compute and spend-ledger provenance. Commit and push small evidence and implementation; delete only P2B_PROMPT7.md at completion and STOP.

Pre-policy review clarification: preserve distinct design replay seeds by moving to the next admissible design-list entry if the hash-selected entry equals the primary seed. Fresh-gate primary/replay populations are disjoint. An initially drafted list router omitted this historical collision avoidance; a failing prospective test exposed it and the router was corrected before any round-three policy run.

## Construction-only measurement, before Docker or policy runs

- design 1000000..1000999: 1/1000 exhausted all 32 candidates (0.1 percent); 1 construction rejections.
- primary 1003000..1003999: 0/1000 exhausted all 32 candidates (0.0 percent); 0 construction rejections.
- replay 1004000..1004999: 0/1000 exhausted all 32 candidates (0.0 percent); 0 construction rejections.

The only rejected seed is 1000075: all 32 candidates report `invalid price-return domain`. Primary is 1003000..1003499 and replay is 1004000..1004999, with no extension or overlap. Full seed lists and rejection diagnostics are in results/p3a3_screen.json. The complete parallel construction measurement took 266.9772972330102 wall seconds. A preliminary serial attempt was interrupted to parallelize construction; its partial console is retained in .cache/p3a3_screen_serial_partial.txt, and the complete measurement reran every declared seed. No policy-based filtering occurred. Extreme-tail construction failures remain excluded, limiting the population to admissible episodes.
