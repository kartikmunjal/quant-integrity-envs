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
