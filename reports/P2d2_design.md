# P2d round 2: prospective reward audit and stop condition

This note precedes any round-2 implementation, tuning, new generated case or
fresh gate. Scope is E6 reward only, with read-only sensitivity inspection of
E1/E5. Generator stays
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.
Frozen weights and all thresholds remain unchanged.

## Actual existing E6 formula

From envs/e6_data_traps/reward.py, let U_p,U_r denote numeric qualities and
A_p,A_r anomaly qualities. The code computes

    R = U_p*A_p*U_r*A_r*(0.6*U_p + 0.4*A_p).

Anomaly quality enters in both execution couplings and again in the weighted
anomaly component. On corrupt cases A=F1^32. With exact reconciliation and equal
primary/replay F1=f, the reward is

    R = 0.6*f^64 + 0.4*f^96.

There is no single effective exponent: the reconciliation contribution has
exponent 64 and the anomaly contribution exponent 96. If only primary F1 is
imperfect, the powers are 32 and64; if only replay F1 is imperfect, the power is 32.
The roles are asymmetric.

For near_false_flag on T1, one true corruption is found and one false flag is
added: precision=1/2, recall=1, F1=2/3. Both executions use that policy, yielding
0.6*(2/3)^64+0.4*(2/3)^96, about 3.22338e-12. This is repeated application of an
already steep F1^32 transform, rather than a small direct penalty for one error.
The existing gate artifacts remain historical and will not be edited.

## Read-only E1/E5 audit and mandatory stop

E1 computes 0.8*p*r+0.2*p*r^2. With equal numeric quality q on both executions,
this is 0.8*q^2+0.2*q^3 rather than q. E5 computes a shared p*r coupling, then
multiplies each weighted field quality and the replay quality again. With equal
quality q for both reported numeric fields on both executions, its reward is
q^3. Both therefore show the same repeated-quality compounding pattern.

P2B_PROMPT.md step 2 explicitly says: "If E1 or E5 shows the same compounding
problem, stop and tell me before changing anything." That condition is met.
Complete the read-only sensitivity tables, record the finding, then STOP.
Do not redesign or tune E6, fix its diagnostic, edit AMENDMENTS.md, freeze/run a
new gate, or change E1/E5. No independent new-reward implementation/validation
session is started because the new-reward stage is not authorized after this
stop condition. Documentation and sensitivity artifacts may be committed/pushed
under the prompt's reporting instruction.

## Requested future E6 desiderata, recorded but not tuned

If the owner authorizes continuing after this finding, the requested combination
is min(R_primary,R_replay), with the anomaly term applied once and frozen 0.6/0.4
weights. Before any tuning, require:

- Five of six corruptions found, no false flags and exact reconciliation: >=0.5.
- Every true corruption found with one false flag: >=0.2 on T1 and >=0.5 on T3.
- Every conceptual wrong mean <=0.10, individually and in aggregate.
- Every cheater mean <=0.05; reward monotone in F1.
- T4 clean-gap diagnostic exactly matches its prospective definition.

No modest exponent or replacement formula is chosen in this stopped audit.
Design seeds 1002000..1002999, primary 1003000..1003499 and replay 1004000..1004999
are reserved for an authorized continuation; none is generated or evaluated now.
The requested amendment following the first E6 gate, prospective tests,
independent validator/reviewer, freeze, one-shot gate and 50 author-reviewed
trajectories are deliberately not begun. No P3, model, sealed evaluation, API
or GPU work occurs.

## Owner-authorized continuation from P2B_PROMPT1.md

The owner explicitly resolves the step-2 stop: keep E1/E5 code, reward, gates
and freezes unchanged; their sensitivity tables remain documentation only.
Proceed with E6 from step3. The earlier audit/stop record above is historical.

Before tuning, fix this per-execution structure. U is the existing numeric
quality; A=F1^p for corrupt cases, A=(1+false_flags)^(-p) for clean cases.
Use a single shared conformance cap B=min(U,A), then

    S = B*(0.6*U+0.4); R=min(S_primary,S_replay).

A enters once, through B: no execution-product and no extra anomaly multiplier
in the weighted sum. The0.6 contribution measures reconciliation quality under
that cap; the0.4 contribution measures conformance itself. Exact reconciliation
gives S=A; numeric-only errors give S=0.6*U^2+0.4*U. This remaining numeric shape
is explicit, and is not claimed to be linear. Pure additive0.6*U+0.4*A would
retain0.6 for exact tables with entirely wrong flags, violating the unchanged
conceptual-error ceiling; the common cap prevents that.

Choose p only from the prospective modest grid1,2,3. Select the smallest p that
meets every per-tier individual/aggregate wrong-policy ceiling on the entire
design partition, all cheater checks and every previously stated sensitivity
desideratum. Do not change construction/corruption data to make rewards pass.
If no candidate qualifies, report failure and stop rather than extend the grid.
Monotonicity follows because min(U,A) is monotone in A, with nonnegative weighted
factor; test boundary and counterexample fixtures independently.

Keep schema, corruption construction and physical runtime unchanged except seed
routing for this round and fixing the T4 diagnostic to the written clean gap
max(numeric_error,1-1/(1+false_flags)). Preserve first-gate artifacts byte-for-byte.
New paths use p2d2 names. Commit design/tests before primary changes; dated
amendment attests the first E6 result was seen but no baseline/sealed/model
result exists. Design1002000..1002999, primary1003000..1003499 and replay
1004000..1004999 only. The original E6 design/gate ranges remain historical.

Prospective gate:500oracle/tier;50per other control/tier. Add find_k policies
for every k=0..6, retaining the first min(k,n) actual repaired flags; report n
and k separately, including T4 n=0 (all such exact clean controls valid).
The numeric near controls and one-false-flag diagnostic remain. All gate cases
are independent normal v1 rollouts; both all500 and first50 oracle groups count.
Independent checker agreement includes actual parsed answers and separate hard-
gate variants; record50full trajectories for author review. Freeze source,
design,image and candidate study before fresh results, then run once with no
post-result tuning or episode dropping. Check implementation CI if accessible,
otherwise give its exact commit hash to the owner. STOP before P3.
