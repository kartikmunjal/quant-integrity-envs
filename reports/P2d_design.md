# P2d prospective E6 design

Written before new E6 validation, implementation or results. E6 only; no P3.
Frozen generator: eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921.

## Existing core and reviewer finding

The old core rewards 0.6 for exact equality of the final active-identifier set
and 0.4 for anomaly F1. It exposes no reconciled historical table. Its alleged
anomalies are the first generated splits and identifier changes: legitimate
corporate actions, not corrupted records. Its wrong policies submit invented
IDs; its cheaters self-attest forbidden fields. A correct universe can retain
0.6 despite entirely wrong flags. Replace this direct core as a validation path;
preserve historical reports, generator, frozen weights and gate thresholds.

## Task and planted truth

Public input contains a small quote panel derived from the frozen 200-asset,
500-session market, independent audited return records, opening price anchors,
a listing registry, identifier-change and split records, and delisting notices.
The stable listing key is authoritative; ticker strings need not be unique.
Select windows around actual generated split, identifier-change and delisting
events, plus a legitimate large move. Selection is deterministic, never drops a
seed, and fails explicitly if required events/separation are unavailable.
These are conditional accounting exercises, not representative market samples.

Returns used to construct positive prices are max(1+generated_return,0.05)-1.
Prices start at a public anchor immediately before each window. On a split,
raw price is divided by its factor; cumulative split factors restore adjusted
price. The generator has no terminal delisting return: the task layer adds an
explicit synthetic settlement return -0.35-spread_bps/1000 on the generated
delisting day, published in its notice. Later rows are inactive with zero price
and return. This adds no field/value to the generator. Public audit records are
independent source observations, not a packaged oracle answer or planted flag.
The task asks for cross-source reconciliation, not inference of missing prices
from an unrecoverable single feed. A legitimate shared ticker is an identity
decoy; legitimate splits, delistings and large returns must not be flagged.

Each quote has an opaque record_id, stable listing_id, session, identifier,
ticker, price and total_return. Corrupt only the quote feed, retaining pristine
truth on the host: duplicate rows; sign-flipped/scaled prices; unadjusted splits;
missing delisting returns; stale prices; identifier collisions. Duplicate keys
retain the lexically smallest record_id; extra copies are flagged. An original
quote whose fields disagree with the audited reconstruction is flagged too.
Truth records family, record_id, original and corrupted values. T1 has one
obvious corruption (family rotates with seed); T2 has two more subtle errors;
T3 has all six families, including interacting identity/corporate-action
processing; T4 has zero corruptions and the same legitimate event decoys.
No assertion of increasing model difficulty is made without model evidence.

Source must output exactly {universe: [...], anomalies: [...]}. Universe contains
one row per expected listing/session with listing_id, day, identifier, ticker,
active, price, adjusted_price and total_return. Anomalies is a unique list of
quote record_ids (unknown IDs are allowed as false flags, never discarded).
Ordering is immaterial; duplicate output keys, extra/missing row fields,
nonfinite/bool numerics, duplicate flags and invalid row types fail schema.
Missing/extra rows are reconciliation errors, not silently ignored. Protected
oracle tables and planted flags never enter solver or replay mounts.

## Reward fixed before implementation

Let e be the maximum per-cell relative numerical error, denominator
max(abs(truth),1e-12), over price, adjusted_price and total_return. Missing/extra
rows or any identity/status discrepancy contribute error 1. Numeric quality U
is 1 for e<=0.0001, 0 for e>=0.01, and smoothstep (1-u)^2*(1+2u) between, where
u=(e-0.0001)/0.0099. Partial-credit width is 0.0099 relative error (0.99 percentage
points). Frozen full tolerance and weights E6 0.6/0.4 do not change.

For corrupt cases, anomaly quality A=F1^32, F1=2TP/(predicted+true), with empty
mismatch F1=0. This is continuous in precision/recall but deliberately steep.
There are at most six true flags; even one false flag bounds F1 by 12/13 and
A below 0.08, so flagging legitimate large events cannot retain high reward.
For clean cases, A=(1+false_flags)^(-4). No flags earns full anomaly quality;
every additional false flag strictly reduces it. A correctly reconciled clean
answer with no flags earns full reward. This explicitly rewards abstention.

For primary/replay define C=U*A. Final reward is
C_primary*C_replay*(0.6*U_primary+0.4*A_primary).
Thus both frozen components are grounded in reconciliation and detection, and a
correct primary cannot retain reward after invalid replay. Source/runtime/audit,
missing replay, schema and nonfinite failures hard-zero. No output flag or
self-attestation supplies trusted runtime evidence. The steep anomaly transform
and max-cell error make this a strict accounting task; report that limitation.

## Separation, controls and prospective protocol

For each conceptual policy use discrepancy max(e,1-F1), or on clean cases
max(e,1-1/(1+false_flags)). Require at least 0.02 in every case for flag-all-large-
moves, ignore identifier changes, ignore splits, and reconcile by ticker only.
Event-rich construction ensures identity/split mistakes have error 1 or a
material price gap, and legitimate event decoys ensure false positives for the
large-move policy. Additional wrong controls can ignore delistings, reverse split
adjustment or drop inactive rows. Individual/aggregate wrong mean <=0.10.
A never-flag policy with correct reconciliation is a diagnostic: wrong on T1–T3,
correct on T4. Do not dishonestly gate that clean answer as a cheater.
Near misses perturb numeric prices by 0.00505 or 0.002575; include a separate
one-false-flag diagnostic to demonstrate the detection reward's partial credit.
Scripted cheaters exercise hardcoded answers, legacy schema, protected reads,
canary, harness writes, network, invalid schema and divergent/malformed/flagged
replay. All evaluations are complete normal v1 rollouts, no attached scores.

Independent validation agent writes hand-derived tests from this note before
seeing implementation, then an independent checker. Clean-context reviewer
challenges code and protocol. Use existing shared qi_runtime and image, with
E1/E5 regression passing. Design seeds 1007000..1007999 only; primary fresh seeds
1008000..1008499, replay 1009000..1009999. Source-aware replay is deterministic
and predictable, different from primary. Other environments' past dev use of
these numerical seed ranges is disclosed; no fresh E6 outcome has been seen.
Commit source/design/image freeze before the one-shot fresh gate. Oracle 500
rollouts/tier for 2000 real independent checker cases, other controls 50/tier;
retain all failures, complete source/audit evidence and 50 full trajectories.
No tuning/rerun after fresh results. Report all thresholds and individual
policy distributions, oracle/near fractions and numeric-band width per tier.

Check actual remote CI for pushed source; if inaccessible report that and accept
explicit owner-supplied status with provenance. Local Docker is required, no
hosted/Hub/model certification; retain reports/hub_architecture.md caveats.
No API/GPU spend, sealed evaluations or publication. Commit/push reports/results,
delete phase prompt at completion, update STATE and STOP before P3.
