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
