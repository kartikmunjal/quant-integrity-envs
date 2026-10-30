# E3 round-two independent validation review

Independent author: `/root/p3b_validation`. Date: 2026-10-30.
This review concerns development evidence, not a completed environment gate.
The round-two owner decisions resolve the earlier all-null/final-propriety
contradictions. The present finding is failure of this construction and solver
design, not proof that the revised contract is mathematically impossible.

## Independent stored-vector audit

Reproduce with:

```sh
.venv/bin/python tests/validation/e3_round2_vector_audit.py
```

The resulting `results/p3b2_independent_vector_audit.json` binds its input summary
and audit source hashes. It verifies all nine recorded source hashes, seven
compressed-shard hashes and byte/row counts, then recalculates every reward from
stored probabilities and truth using the independent polynomial-integral
checker. It imports no production reward helper, policy, generator or runtime.
No new episode or policy is run by the audit.

Evidence environment: E3; generator version
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.
All numbers below are reproduced from that results file and its input
`results/p3b2_design_vectors.json` and shards.

- Verified 172 cases, 5,504 stage rewards, 2,752 combined policy rewards and
  2,064 honest-minus-wrong gaps. Every stored reward and gap agrees within
  absolute tolerance 1e-12.
- 119 cases fail the required .02 gap: T1 38, T2 34, T3 31, T4 16.
- Worst wrong-policy means exceed .10 on every tier: T1 .620155
  (`bonferroni_trials_ignore_correlation`), T2 .534884 (`top_k`), T3 .273902
  and T4 .390181 (both `bonferroni_trials_ignore_correlation`).
- The T2 shallow score .534884 exceeds its .30 ceiling. T3 shallow .240310
  passes that diagnostic.

The design-vector population is the complete committed screened design list,
not a subset chosen after observing policy reward. The audit checks arithmetic,
stored-output schema correspondence, manifests and aggregate reporting. It does
not independently regenerate the underlying synthetic market, certify the
normal likelihood, establish submitted-source execution equivalence, or replace
a checked-container gate. The `hardcoded_ids` vector fixture deliberately uses
the primary honest snapshot unchanged on replay, so replay IDs fail schema;
this is a mathematical lifecycle model, not a host execution of its self-editing
submitted source.

## Diagnosis and stopping implication

Structural decoy ordering does not imply policy-reward separation. The actual
data remain solvable by several simpler or incorrectly specified policies.
In particular, top-half ranking retains substantial signal on T2, and the
Bonferroni policy that ignores correlation performs well enough across all
tiers that calling it conceptually wrong does not make its reward small.
That is the shortcut failure these controls were intended to detect.

The honest normal-max likelihood uses an effective trial count and a normal
approximation for static signed portfolios, heterogeneous market variance and
group-shared paths. Its effect scale and dependence approximation need not
yield calibrated probabilities. It is therefore plausible for hard classifiers
or ranking policies to outperform this reference under the clipped score.
This is a diagnosis consistent with the results, not a demonstrated causal
attribution: no post-result ablation or tuning was performed in this review.

The recorded honest means (.490569, .502964, .334173, .492626 for T1 through
T4) clear the prospective reference floors, but that does not repair failed
wrong-policy ceilings or per-case gaps. A low-enough reference floor is not
evidence of robustness to the required conceptual mistakes.

The structural screen was explicitly provisional. Since its promised gap
validation fails, it cannot be relabelled successful final case admission.
There is no valid basis for the source/design/image freeze, stress certification
or one-shot gate under this design. Do not remove failing seeds or change
thresholds. The committed design disallows effect/search/correlation tuning
after policy results; a revised construction requires an owner-authorized,
prospective design with retained failed evidence. Additional implementation
checks may establish the behavior of already-written code, but cannot be
reported as completion of the requested E3 phase.

## Independence and limitations

Reward tests/checker were committed before reward implementation. Case tests
were independently written before this author inspected the case source, but
the implementation author had already written uncommitted cases; that specific
tests-first deviation must remain visible. Later inactive-asset, diversification,
source-drift and presentation corrections received independent prospective
tests. This author neither implemented the production verifier nor edited its
source.

The candidate template is synthetic and narrow, with fixed K=20 and ten real
candidates. Public common-effect metadata supplies privileged knowledge of the
generating scale, although it does not expose individual membership. T4's
committed schedules make N=1 a real-membership shortcut. The content-derived ID
wrapper removes the earlier cheap seed-hash inversion; it does not establish
cryptographic secrecy against full generator enumeration. Replay is predictable.
Normal-max probabilities remain approximate. These limitations persist even
when unit tests pass.

Audit spend: API $0, GPU $0. No stress, freeze, sealed evaluation or one-shot gate
is certified by this review.

## Subsequent independent sensitivity and fixed-case audits

`results/p3b2_independent_sensitivity_audit.json` independently verifies every
retained transform mean, reliability bin and false-admit count without new
episodes. The maximum incentive gains are .031836 on T1 and .094058 on T4,
both above the allowed .02. T2 .014250 and T3 .014982 pass. All four best
transforms move probabilities toward one with multiplier .75. This confirms an
additional design failure; the transformed policies were not adopted.

`results/p3b2_exact_wrong_audit.json` records 32 unique fixed cases where an
ordinary wrong policy's predictions equal truth on both primary and replay:
16 T1, 13 T2, one T3 and two T4. There are 50 matching policy/case pairs.
The first is seed 1000000/T1, replay 1005276,
`bonferroni_trials_ignore_correlation`. Its exact raw loss is zero on both
stages, hence its mathematical final reward is one. No honest solver with
reward bounded by one can beat it by .02. Thus changing only the honest solver
cannot repair the current fixed-case gap failures. This does not prove that
every possible new construction would fail.

## Independent audit of the checked smoke

`results/p3b2_independent_smoke_audit.json` is reproduced by
`tests/validation/e3_round2_smoke_audit.py`. It verifies the committed smoke
source hashes, all 96 compressed raw-record hashes and lengths, planned row
identities, initial source hashes, independent raw-answer reward agreement,
immutable image identity, nonempty audited command evidence, stage source-hash
consistency, container uniqueness and recorded cleanup. All 96 rewards agree
with the separate polynomial-integration checker within 1e-12. There are 232
distinct containers and 68 primary/replay pairs; invalid or flagged solver
submissions correctly stop before protected re-execution. All rows completed
without retry. Expected policy-violation exceptions are retained in journals;
they are not infrastructure failures.

All eight cheaters receive zero on all four smoke tiers. The four protected
access/tamper/network attacks are solver-flagged and have no primary or replay
execution. Primary-only oracle snapshots pass primary and fail replay schema
on each tier. The self-editing hardcoded-ID policy similarly retains a valid
primary answer and fails replay IDs. Its transferred source hash differs from
initial source and agrees between primary and replay, as intended. Transferred
self-edited source bytes are not retained, so the audit establishes recorded
hash agreement and observed outputs rather than independently reconstructing
every transferred byte. Raw records establish recorded commands and flags;
this is not a fresh independent Docker inspection.

This fixed first-design-seed smoke checks the local implementation's lifecycle
and defenses. It is not stress certification, a one-shot gate, a robustness
estimate over the gate population, or a substitute for the failed construction
and incentive requirements. No new episodes were run by these audits. The
recommendation remains a stop before freeze, stress and gate.
