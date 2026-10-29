# Independent final-runtime historical regression review

E1 verdict: **PASS, 1,000 of 1,000 exact reward matches.** Reproducible audit evidence is `results/p3a2_e1_regression_audit.json`. This is an independent coding-agent file audit, with no Docker workload, paid call or source/test edit. E5/E6 are not inferred from E1 and remain pending.

The E1 summary binds implementation `aa86c69801a07c8aaf627a6336503235e90e9fdf`, runtime `fad402d113ca9e19f082ac45e3e0904edb128b9e672c351fe3a2d62eb699a827`, and generator `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`. I verified every bound source against that immutable commit, all row/manifest shards, all 1,785 local manifest files with exact tree coverage, all 1,000 raw rollout records, and every referenced exception part/hash.

The exact selection-list bytes equal the prospectively committed `25ebb4f` artifact. Every planned index appears once with the fixed policy/tier/seed identity and original baseline-file hash. All historical expected rewards match both raw and compact new rewards by exact numeric equality, and all 1,000 original replay-seed values also match. The complete tier/policy stratum counts are preserved in the audit JSON. The runner did not resample or omit a row.

Every row completed healthy without retry, and every attempt completed cleanup without resource overlap. All 2,652 created container IDs are unique and have matching removals. Independent raw telemetry recomputation matches every compact record and the summary: 26,084 transfers/probes, zero timeouts and failed probes, maximum transfer 7.419414852978662 seconds and maximum probe 2.170218621031381 seconds. Experiment wall time is 1373.8363803810207 seconds; audit elapsed CPU time is separately recorded in JSON.

The lowercase physical summary `results/p3a2-regression-e1.json` and canonical uppercase registry alias `results/p3a2-regression-E1.json` are byte-identical, including SHA256. Their raw, manifest and shard references consistently retain the lowercase physical paths. This is a filename alias of one measured outcome, not a second experiment. The earlier uppercase-tag initialization error occurred before rollout and is retained separately; it is not a reward difference or an excluded measured episode.

E1 success does not override E2's failed stress-completion prerequisite. Freeze remains blocked; this review authorizes neither a fresh gate nor a scientific admission change.
