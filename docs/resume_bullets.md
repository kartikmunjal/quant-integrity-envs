# Resume bullets: validated synthetic infrastructure only

- Built and locally validated 3 synthetic quantitative-integrity tasksets across 4 tiers, completing 21,800 scripted numerical-gate rollouts with independent checker agreement of 100%. Sources: `results/p2b2_gate.json`, `results/p2c_gate.json`, `results/p2d3-gate-E6-c12.json`.
- Validated checked Docker execution across 30,000 E1/E5/E6 stress rollouts at concurrency 12 and 24, retaining every planned row and recording 0 retries. Sources: `results/p2d3-r2-stress-{E1,E5,E6}-c{12,24}.json`.
- Verified exact reward preservation on 3,000 stratified historical rows after shared-runtime infrastructure corrections, with 1,000 comparisons per taskset. Sources: `results/p3a2-regression-e1.json`, `results/p3a2-regression-e5.json`, `results/p3a2-regression-e6.json`.

These describe scripted local validation, not model performance, training or real-market profitability. Mutation-engine/E2 validation remains blocked and is not claimed as completed. All measurements use generator `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`. Gate and original stress runtime provenance is in each named result; corrected-runtime regressions use `fad402d113ca9e19f082ac45e3e0904edb128b9e672c351fe3a2d62eb699a827`.
