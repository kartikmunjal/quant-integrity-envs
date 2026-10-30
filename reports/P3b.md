# P3b: E3 design preflight blocked

STOP before implementation. E3 (`qi-fdr-adjudication`) was not built, screened, stressed, frozen or gated. The requested all-null construction and per-case separation requirements conflict. No frozen requirement was relaxed to produce a passing result. This is a mathematical preflight failure, not a failed or consumed one-shot gate.

## Work and provenance

Baseline: `2f614c5a8ba06928dbc71bf13153269bde31a93b`. Design and dated amendment committed first at `fa305dfffd5b703c37e58a7aa48111b357e16e6e`. The later report commit contains the independent diagnostic tests, checker, recorded mathematical results, partial seed inventory and this report; its hash is available from `git log -1 -- reports/P3b.md`.

Read [design](../docs/e3_design.md) and [independent feasibility review](../docs/e3_feasibility_review.md). Independent validation author `/root/p3b_validation` reviewed the mathematics and authored the diagnostic tests/checker after the design commit. The proposed implementation author did not edit those tests/checker. No production verifier was authored, so this does not constitute independent validation of an E3 environment.

All phase evidence concerns mathematical fixtures or historical seed records, not environment performance. Generator identity remains `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`; it was not executed. Shared runtime, generator, existing environment sources, historical freezes and thresholds remain unchanged.

## Blocking findings

On required all-null truth, reject-all submits the optimum probability vector. An honest reference cannot beat that optimum by 0.02 on the same constructed case. Identical reports cannot receive different rewards based on policy labels under the requested output score. Giving every all-null report zero also leaves separation zero. This contradiction does not depend on how rare all-null episodes are. Oracle and wrong-policy mean gates alone are not claimed to be contradictory at every possible tier composition.

The requested clipped reject-all-relative normalization also does not preserve strict propriety for the usual continuous finite-endpoint additive proper scores. With eight candidates and complementary half-null truth states, a sufficiently confident deterministic report has higher expected clipped reward than truthful marginal probabilities. The independent diagnostic checker records an exact rational counterexample for the illustrative asymmetric weighted proper loss. Raw loss propriety and the 3:1 Bayes threshold can hold while final reward propriety fails. This is not a universal impossibility theorem for every conceivable nonadditive scoring rule; the all-null separation conflict already blocks the supplied contract independently.

## Gate disposition

| Criterion | Required value | Measured / disposition |
| --- | --- | --- |
| All-null per-case honest vs reject-all gap | >=0.02 | Impossible under proper scoring; at most 0 |
| Raw propriety and 3:1 threshold | Truthful optimum; admit above .75 | Analytic derivation and independent mathematical diagnostics; illustrative rule only |
| Final clipped reward propriety | Strictly proper | Counterexample documented; no rule adopted |
| Oracle, T1/T2/T3/T4 | >=.95 each | NOT RUN |
| Random, T1/T2/T3/T4 | <=.05 each | NOT RUN |
| Each of >=12 wrong policies, each tier | <=.10 | NOT RUN |
| Each of eight cheaters, each tier | <=.05 | NOT RUN |
| Honest reference, each tier | Predeclared justified floor | NOT ADOPTED / NOT RUN |
| Shallow detector, T2/T3 | <=.30 | NOT RUN |
| Independent execution/reward checker | >=.999 agreement | NOT RUN; diagnostic mathematical checker is not this gate |
| Oracle and honest clean false positives | <=.02 | NOT RUN |
| Honest reliability calibration | Design-seed test | NOT RUN |
| Construction admission screen | Before any policy execution | NOT RUN; no admitted/excluded population or rejection count |
| Stress C8 and C12 | 5000 each, zero retries expected | NOT RUN |
| Fixed 50 trajectory author reviews | Selected before freeze | NOT RUN; no trajectories or reviews fabricated |
| Source/design/image freeze and one-shot gate | Committed before gate | NOT CREATED / NOT RUN |
| Independent raw execution reward audit | Stored gate executions | NOT RUN |

No episodes were dropped or seeds rejected. No all-null exception, score, tier frequency, effect parameter, honest floor or E3 seed range was adopted. The dated AMENDMENTS entry records only this preflight disposition and explicitly changes no frozen value.

## Diagnostic validation

The independent [evidence](../results/p3b_preflight_math.json) records 2,100 strict raw-loss grid comparisons and 206/206 exact agreements with the separate mathematical checker. For the K=8 asymmetric weighted-score fixture, truthful expected clipped reward is 221409/250000 (0.885636), below the deterministic report's 9/10 (0.9). These are mathematical fixture values, not policy performance. Reproduction: `.venv/bin/python tests/validation/test_e3_preflight_math.py`; verification: `.venv/bin/python -m pytest tests/validation/test_e3_preflight_math.py -q`. Both tests passed; [JUnit record](../logs/p3b_preflight_junit.xml). Initial use of bare `python` failed because that executable is absent; the independent author also recorded an initial missing-evidence-file test failure before generating the fixture with the repository interpreter. These were tooling/order failures, not hidden E3 rollouts. No full regression suite was run because production code was unchanged.

## Seed review

[Partial inventory](../results/p3b_prior_seed_inventory.json) retains source hashes and observed seeds from one historical shard in each listed prior gate. For example, an E1 shard contains replay seeds spanning 1003042 through 1009938, and an E6 shard contains primary seeds 1008000 through 1008049. These are observed endpoints, not a claim that every intervening integer was used. This establishes that simply choosing the high development partition is unsafe. This partial inventory does not prove that no valid unused subranges exist. An exhaustive inventory and reservation remain required after the scoring contract is resolved. No prior seed routing was changed.

## Interpretations, limitations and next decision

The construction gap was read literally as a per-case requirement applying to each listed wrong policy, including reject-all on required all-null cases. Strict propriety was evaluated separately for the raw rule and its final clipped transform. The owner must specify any intended exception for optimal constant controls and whether propriety applies only to the raw score or also the final reward. Possible alternatives in the design note are proposals, not adopted amendments. No full return-generation design can honestly be called approved yet.

The surprise was that feasibility fails before data generation or execution, despite the earlier phase workflow being usable. Predictable replay, a single synthetic candidate template, scripted rather than model solvability, and local Docker would remain limitations of a future implementation; none has been empirically validated here.

## Spend and compute

[Activity record](../logs/p3b_preflight_activity.json): paid spend $0, model calls 0, GPU calls 0, Docker rollouts 0, sealed evaluations 0. `logs/spend.csv` does not exist; no paid call was made, so no model spend ledger entry is fabricated. Compute was local file inspection and mathematical diagnostics; total session wall time was not metered. At the design-commit snapshot tracked files totalled 681,915,900 bytes and `.git` measured 131,212,278 bytes. These snapshot values exclude subsequent report artifacts and are not final repository-size claims.

The requested prompt file is deleted at completion; owner file P2B_PROMPT1.md is preserved. Commit and push record the blocked work. No next phase begins.
