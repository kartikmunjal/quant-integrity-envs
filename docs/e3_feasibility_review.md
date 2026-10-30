# E3 independent mathematical feasibility review

Date: 2026-10-30. Author: independent validation agent
`/root/p3b_validation`, separate from the proposed implementation author.
Scope: mathematical review of P2B_PROMPT10.md, before E3 implementation,
validation tests, construction screening, policy execution, or gate results.
No E3 policy results were inspected or produced. No data seeds were used.

## Finding: requirements need an owner decision before implementation

The raw proper score and its proposed bounded reward transformation must be
distinguished. Strict propriety of a raw score does not imply strict propriety
of an outcome-dependent, clipped, reject-all-relative reward. In addition,
all-null truth makes the oracle and the reject-all constant policy identical.
An output-only verifier cannot reward one while penalizing the other on that
same case. These are mathematical observations, not measured gate failures.

## All-null indistinguishability

Write the truth vector as y and the submitted probability vector as q. On an
all-null episode, y=(0,...,0). A truth-reading oracle submits q=y. The
reject-all policy submits exactly the same q. Consequently every deterministic
output-based scoring function R satisfies

    R(oracle output, y) = R(reject-all output, y).

For any strictly proper raw score S whose deterministic-truth optimum is the
truth vector, the specified normalization denominator on this episode is

    S(y,y) - S(0,y) = 0.

Assigning the oracle value 1 to the common output necessarily gives constant
reject-all value 1 there. Assigning it value 0 to prevent free constant-policy
reward necessarily gives the oracle value 0 there. Returning another value
does not distinguish the identical outputs. Examining source to discriminate
the two would cease to be the stated single proper probability score and does
not solve their behavioral equivalence.

The per-tier gates are means, not per-episode bounds; this distinction matters.
If all-null executions are a fraction a of a tier and receive zero even for the
oracle, a perfect oracle on all remaining executions has mean at most 1-a.
Thus the .95 oracle mean gate fails whenever a>.05. If both primary and replay
are all-null on fraction a and their common output instead receives 1,
reject-all mean is at least a, so the .10 wrong-policy mean gate fails whenever
a>.10. A min across the two executions preserves identical outputs and scores
on all-null pairs. These bounds depend on the declared population and do not
assert a population frequency that has not been specified or measured.

There is a separate, stronger conflict that does not depend on either mean
gate or the all-null population frequency. The construction requirements say
the honest reference must beat **each** wrong policy by at least .02 in
normalized reward on a constructed episode. Reject-all is explicitly one of
those wrong policies. On all-null truth, reject-all is the deterministic-truth
optimum of a strictly proper score. No honest reference can exceed that optimum,
and applying a monotone normalization cannot reverse the ordering. A special
zero-denominator rule preserving that optimum can at best make the reference
tie reject-all, giving gap 0 rather than .02. A rule making another report
strictly better instead abandons proper all-null scoring. Thus the required
per-construction gap is incompatible with the required all-null construction,
even if those episodes are rare enough to satisfy the oracle mean gate. The
same issue arises on all-real cases for the required admit-all wrong policy.

On all-real episodes, the analogous identical-output pair is oracle/admit-all.
The reject-all-relative denominator is positive there, so the division itself
is well-defined; any interpretation forbidding reward to every constant policy
on every episode is nevertheless incompatible with correctness on all-real
and all-null episodes.

## Explicit clipped-normalization counterexample

Consider two candidates with exactly one real. Let Y=(1,0) with probability
.9 and Y=(0,1) with probability .1. The honest marginal probabilities are
q=(.9,.1). Use the strictly proper raw negative Brier score

    S(q,y) = -sum_i (q_i-y_i)^2.

For either possible outcome S(0,y)=-1 and S(y,y)=0, so the required reward is

    R(q,y) = clip(2 q dot y - sum_i q_i^2, 0, 1).

At the honest q=(.9,.1), the two raw normalized rewards are .98 and -.62;
clipping gives .98 and 0. The expected reward is .9*.98=.882.
The dishonest report q=(1,0) receives rewards 1 and 0, with expected reward
.9, strictly larger. This counterexample has no zero denominator, no real
market data, and no uncertain numerical integration. Its exact rational
arithmetic demonstrates failure of propriety after the requested transform.
It is not a claim that Brier alone is the required 3:1-weighted score; rather,
it disproves any general argument that raw propriety survives this transform.
A different proposed raw score must prove propriety of the final transform
separately if that is intended as a requirement.

The clipping problem also applies directly to the allowed candidate count and
to regular asymmetric binary scores, rather than only the two-candidate Brier
illustration. Assume the usual additive candidate score, with one common
continuous strictly proper binary score s, including the regular weighted
families proposed in the prompt. Take K=8. State A has the first four candidates
real and the last four null; state B has the complementary truth. Set
P(A)=p and P(B)=1-p. Each state has four real candidates, so its reject-all to
oracle denominator is the same positive quantity

    D = 4 * (s(1,1) - s(0,1)).

The deterministic report q=A has normalized reward 1 on A. On B its score minus
reject-all score is

    4 * (s(1,0) - s(0,0)) < 0,

since deterministic null truth uniquely prefers probability zero. Its clipped
reward on B is therefore zero, giving expected reward p. The truthful marginal
report q_p has first four probabilities p and last four probabilities 1-p.
As p tends to 1, continuity implies its normalized reward on B remains negative
for all sufficiently large p<1 and is clipped to zero. On A its reward is
strictly below 1 because q_p differs from deterministic truth. Therefore

    E[R(q_p,Y)] = p * R(q_p,A) < p = E[R(A,Y)].

Thus clipped final-reward propriety fails for this entire common additive,
continuous, strictly proper class, including an asymmetric score chosen to
emphasize the .75 decision region. Both outcomes have half-null composition;
no all-null convention or outcome-dependent denominator is involved. This
argument assumes continuity at deterministic reports and finite endpoint scores;
an unbounded score excluding those endpoints needs a separately specified
oracle and normalization and is not covered by this continuity proof.

An additional generic caution: if a zero-denominator convention assigns
R(q,0)=0 for every q in a scalar problem, then for true probability p>0,
expected reward is p*R(q,1). Its maximizing report is independent of p.
It cannot uniquely equal p for every p in (0,1). Thus simply assigning zero to
all all-null submissions cannot repair strict propriety of the final reward.

## What the 3:1 threshold does establish

With posterior probability p, admitting incurs expected classification loss
3(1-p); rejecting incurs loss p. Admit is preferred exactly when p>.75.
This decision threshold is consistent with calibrated probability reporting
under any strictly proper raw probability score. It does not by itself prove
that an asymmetric weighted loss is proper, that a normalized clipped reward
is proper, or that all the requested wrong-policy ceilings are attainable.

## Required disposition

Do not implement a zero-denominator exception, alter a frozen gate, omit clean
episodes, or claim final-reward propriety silently. The owner must clarify
whether strict propriety is required only of the raw score or also the final
reward, what reward correct all-null outputs receive, and how that interacts
with the constant-policy requirement and tier composition. The implementation
author has been informed of these conflicts before any E3 design or outcome.

No implementation, validation tests, second checker, policy execution, Docker
work, model call, or paid compute was performed for this review. Spend: $0.
