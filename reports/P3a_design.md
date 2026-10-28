# P3a prospective design: mutation engine and E2

Written before P3a implementation, mutation execution, effect measurement, reward
selection or fresh results. Authoritative inputs are SPEC.md, prereg.yaml and the
owner's P2B_PROMPT3.md. Only the mutation engine and E2 are authorized. E3, P4,
P5, model pilots, training, M1 packaging, rename and public release remain outside
this phase. Milestones were committed first in 030cff9b448fbbde18b8d29c7f32283e306feb7f.

## Fixed boundaries and interfaces

Keep the frozen generator/version, existing E1/E5/E6 sources, financial weights,
tolerance and gate thresholds unchanged. Use synthetic generator data only.
Implementation lives in src/qi/mutate/, envs/e2_leakage_audit/ and an E2 plugin,
with supporting phase scripts/tests. Reuse CheckedRuntime, immutable image
sha256:9cc803aaddbbb1a17c9eef928b5438d61769c9c9ba928fc285bc7ee622ad8353,
protected host truth, fresh workspaces and the existing whole-rollout retry.
The current core runtime version is
5ac8cf100aabc4d4b47f38fe8ecc4a34fe4db1c77f6042d719c165489769781a.

Public source is a complete executable research script; public data contain
prices, returns, availability-stamped fundamentals, listing/identifier/activity
records and declared train/selection/evaluation boundaries. Do not expose the
case seed, selected mutation IDs, family labels, effect measurements, gold
locations or gold patches in agent-facing metadata/comments. Source and data are
staged only in the solver work directory. Host truth is never mounted.

The research contract returns ordered holdings, fill prices, per-strategy and
selected-strategy return/equity paths, turnover, selected strategy, net summary
statistics and multiplicity-adjusted significance. These are functional research
outputs, not debug mutation sentinels. Stable JSON field names are public APIs;
internal identifiers, function names, presentation and control-flow realizations
vary. Maximum source/patch size is the shared 100000-byte bound.

Proposed host API: qi.mutate.catalogue.CATALOGUE describes twelve operators;
qi.mutate.reference supplies the trusted clean numerical oracle;
qi.mutate.render renders clean/mutant/decoy source;
qi.mutate.cases.make_case(seed,tier,excluded_families=()) returns public material
and host-only provenance. E2 reward/checker modules consume immutable execution
records. Agent-submitted patch source is never executed on the host. Trusted
semantic oracle evaluation uses structured internal choices, not eval/exec of
submitted or arbitrary source text. Generated source is checked by real runtime
execution in mutation validation.

## Reference research and effects fixed before measurements

Generate the existing minimum-sized market configuration (200 assets, 500
sessions), then select a documented event-rich asset/window subset without
changing generator output. The initial task target is twelve assets and a
96-session research window with distinct training, selection and evaluation
segments. Full required prehistory and later records remain available so the
script must enforce availability and temporal boundaries. Candidate windows and
asset subsets are chosen deterministically from at most 32 candidates per seed.
All candidates and rejection reasons are recorded; exhaustion fails the case,
never replaces the requested episode seed or silently drops a gate row.

The clean script fits only admissible training observations, purges training
labels whose horizon reaches the next partition, uses listing identity and
as-of membership, selects a strategy on the selection segment, fills orders at
the next declared tradable close and evaluates on the final segment. It reports
Bonferroni-adjusted probabilities for the declared trial count. Label generation
may legitimately reference later prices when labels are confined to purged
training rows. Backtest decisions never consume those future labels.

For every operator/realization, define effect as the maximum relative change in
its declared functional output group against clean reference output. Numeric
series use maximum absolute difference divided by the maximum clean magnitude
in that series, with a fixed 1e-8 floor; categorical membership/strategy changes
are separately recorded and numeric economic consequences are still required.
**Minimum accepted effect is 0.05 for each of the twelve operators.** A change
only in an internal variable, an unused label, comment or diagnostic is not a
bug. Reject ineffective candidates. For T3, require both joint effect >=0.05
and each planted operator's conditional leave-one-out effect >=0.05. Gold
patches must restore all declared outputs within the frozen 0.0001 tolerance.
A constant/disabled reference case is inadmissible: evaluation holdings and
returns must be nonconstant with a positive reference scale above 1e-8.

| Family | Concrete operator | Required economic/output witness | Minimum relative effect |
|---|---|---|---:|
| F1 temporal lookahead | future-return feature | evaluation holdings and return path | 0.05 |
| F1 temporal lookahead | bypass fundamental availability lag | evaluation holdings and return path | 0.05 |
| F2 statistic leakage | full-sample feature centering | evaluation holdings and return path | 0.05 |
| F2 statistic leakage | full-sample scale/volatility fit | evaluation holdings and return path | 0.05 |
| F3 label overlap | omit the label-horizon purge | fitted strategy's evaluation holdings/returns | 0.05 |
| F3 label overlap | include labels crossing selection boundary | fitted strategy's evaluation holdings/returns | 0.05 |
| F4 universe selection | filter to final survivors | holdings, turnover and portfolio returns | 0.05 |
| F4 universe selection | merge history by current ticker | holdings, turnover and portfolio returns | 0.05 |
| F5 execution timing | same-bar signal execution | fill/holdings and realized return paths | 0.05 |
| F5 execution timing | fill at submission rather than next-close price | fill prices and realized returns | 0.05 |
| F6 selection/multiplicity | choose winner on evaluation data | selected strategy and its realized returns | 0.05 |
| F6 selection/multiplicity | omit trial-count correction | reported adjusted significance | 0.05 |

A mutant is killed only when real execution demonstrates its stated effect and
its ground-truth patch restores the clean outputs. Source differences alone do
not kill mutants. The mutation oracle records family/operator, rendered location,
realization, primary effect, witness group, clean/mutant output hashes and patch.
Keep ineffective/rejected candidates in design diagnostics. Never lower the
0.05 requirement to admit a weak mutant after seeing results.

## Structural separation and leave-one-family-out

F1 changes feature information availability. F2 changes the fitted feature
transform's estimation population. F3 changes the label-horizon/purge relation
between partitions while retaining legal training-only future labels. F4 changes
asset identity/membership. F5 changes order/fill alignment after the signal has
been formed. F6 changes strategy selection or trial-count inference, not feature
estimation. They have different stages, syntax operators, gold patches and
witness groups; there is no shared visible bug_enabled flag or family marker.
Future dependence may still be a useful transferable concept; structural
separation does not prove statistical independence or future LOFO transfer.

For future folds excluding F3, F4 or F6, exclude that family's mutations,
family-cued decoys, labels and diagnostic policy examples from that fold's
training data. Mixed cases containing the excluded family are excluded from
that training fold. Keep host fold manifests separate from public scripts.
Current P3a validates all families, with F3/F4/F6 reported individually; it does
not train models or claim held-out-family model performance.

## Realizations, presentation and decoys

Each of the twelve operators has at least three genuinely different syntactic
realizations: direct indexing/slicing, an equivalent helper/control-flow form,
and a different loop/comprehension/dataflow form. ASTs must differ after stripping
names/locations; renaming or whitespace alone does not count. Apply independent
deterministic identifier renaming, layout variation and unrelated refactors.
Do not label changed lines or expose operator names. Store their provenance only
on the host. Equivalent presentations must preserve the clean result.

Decoys reuse the suspicious surface forms inside correct contexts: future-label
construction used only in purged training; full-sample descriptive statistics
that do not fit the strategy; explicit safe purge/embargo arithmetic; legitimate
as-of membership/ticker handling; delayed fills; training/selection maxima and
proper trial adjustment. T2/T3 include distractors, T4 contains only correct
code plus decoys. Decoys must execute identically to clean reference outputs.
Do not count a decoy merely because it contains a comment or dead token.

The shallow detector is deliberately context-insensitive: regex/token matching
for negative shifts/indices, broad fit/mean/std, survivor/ticker patterns, fill
shifts, maxima and p-value/trial patterns, followed by naive local repairs.
**Its allowed mean reward is at most 0.30 separately on T2 and T3.** Exceeding
that ceiling is a design failure requiring additional correct decoys or genuine
realizations before a freeze; retain the failed design iteration. Do not raise
the ceiling. Record this added diagnostic as a dated amendment before freeze.

The scripted oracle auditor uses public syntax/dataflow semantics and the public
research contract to locate errors and construct a general patch. It must not
read private truth in the solver, copy an oracle manifest into its source, or
infer the chosen mutations from a public case seed. Document the restricted
synthetic-template domain of this audit policy.

## E2 submission and single-entry graded reward

The solver reads research.py and input.json and emits bounded JSON with findings
[{family: F1..F6, line: integer}] and patched_source. Matching is one-to-one:
family must match and the claimed line must lie in the true statement span.
Duplicates and unmatched/sprayed locations are false positives. Reported families
or comments are never accepted as evidence that a patch works.

Let D be matched bug-set F1 raised to a modest exponent p on dirty code. On clean
code D=1, and C=(1+false_flags)^(-p); on dirty code C=1. Thus C measures clean-code
false flags and is not a second copy of dirty detection quality. Let P be a
continuous numeric patch quality: 1 at relative error <=0.0001, 0 at >=0.01 and
a cubic smoothstep between them. Patch error is the maximum normalized error
across all required functional research outputs, with identity/schema failures
at error >=1. Incomplete functionality or constant returns cannot substitute for
the required nonconstant paths and therefore cannot earn correctness credit.

Use the frozen weights once each in a weighted harmonic combination:

    H(D,P,C) = 1 / (0.4/D + 0.4/P + 0.2/C)

If any term is zero, H is zero. Each quality enters once; there are no repeated
products, outside quality multipliers or powers applied to the combined reward.
A perfect bug list with a disabled/constant patch has P=0 and reward zero, meeting
the <=0.05 desideratum. Primary and fresh replay qualities are computed from
actual executions; final reward is min(H_primary,H_replay). Reporting uses the
same primary-source bug list for both stages; the patched program must generalize
to fresh data. Hard schema/security gates remain hard zeros.

Before tuning, fix exponent candidates [1,2,3]. On design seeds only, select the
smallest exponent satisfying every original gate, the shallow ceiling and these
desiderata: exact numeric patches with k of n correctly reported bugs have
strictly increasing grades as k increases, T3 finding two of three scores >=0.5,
and neither one missed bug nor one false flag collapses an otherwise exact patch
to zero. Clean single-false-flag grades must be strictly between zero and one.
Keep all candidate results. If none meets the rules, report design failure;
never change weights, gate thresholds, the grid or these floors post-result.

T1: one obvious bug. T2: one subtle bug plus correct distractors. T3: three
interacting bugs from distinct families plus distractors. T4: clean/decoy source.
Report partial patch and partial detection curves separately. Twelve conceptual
wrong policies insert one of the twelve semantic errors into an otherwise clean
patch, even on T4, and must each and in aggregate have mean <=0.10. Eight cheaters
include constant/hardcoded patch outputs, canary/oracle reads, harness/network
attacks, schema forgery and primary-only replay overfitting; mean <=0.05.
Random mean <=0.05 and oracle mean >=0.95 remain unchanged. A truthful empty
finding list with the unchanged clean script is a semantic clean control, not a
cheater; report its expected T4 reward separately rather than falsely requiring
a correct clean answer to fail. Other controls are shallow detection, find_0..3,
two numeric near patches, false-flag and report-only/disabled-patch ablations.

Future-poisoning is included: replace data after a declared evaluation cutoff
with deterministic noise and compare causal prefix holdings/orders and realized
prefix returns with their unpoisoned values. Later summaries may legitimately
change. Correct training-only future labels remain allowed. Fold the maximum
causal-prefix discrepancy into P's single numeric error; do not multiply a new
quality factor. Apply this check without using it as a family-label shortcut.

## Independent validation first

An independent validation agent reads SPEC and this design, writes mutation-kill,
decoy, reward monotonicity, disabled/constant, schema/security, source/replay,
family separation, presentation diversity and scalar-checker tests before
implementation. Its checker uses an independent matching/scalar numeric path,
without importing reward/helper functions. Record author/reviewer roles plainly.
The author does not claim independent human validation.

Design mutant catalogue exercise: twelve operators times three realizations on
50 design data seeds (1800 accepted mutant executions), plus all correct decoy
and presentation variants. Verify actual runtime outputs, effects and gold patch
restoration. Failed/inactive candidates and exhaustion remain recorded; any
unkilled admitted mutant or misclassified decoy blocks the gate. Also compare
independent scalar checkers on at least 2000 cases, including adversarial records.

## Seed split, freeze and one-shot gate

Design seeds only: 1000000..1000999. No E2 fresh rollout result before a committed
source/design/image freeze. Gate primary 1001000..1001499, replay 1002000..1002999,
derived deterministically from primary seed, tier and submitted patch hash.
Reserve logs/p3a_gate_calls.json exclusively before planning, independent of run
tag or concurrency, including failed initialization. Use complete ordinary v1
Env/Agent/Task rollouts and fresh solver/primary/replay/poison containers. Carry
source hashes and protected truth provenance throughout.

Use 500 oracle cases per tier (2000 actual checker-unit cases) and 50 per other
policy per tier. The exact fixed policy catalogue and population are committed
before fresh results; no case is dropped or silently replaced. Run at concurrency
12. Retain both attempts for an infrastructure retry, with completely fresh
container sets and full cause/context chains. Policy failures never retry.
Unknown or second failures remain terminal. At most one infrastructure retry,
100% completion and retry rate <=0.005 are mandatory; stop on excess. Preserve
all failures, 50 full author-reviewed trajectories and a separate clean-context
review before/after the gate. No fresh rerun or threshold tuning after results.

## Storage, housekeeping and report

Before and after this phase, record tracked worktree bytes, .git disk use, results/
logs/ignored-artifact disk use, git object counts and filesystem capacity in logs.
Do not rewrite history or delete old archives to shrink the repository.

New P3a tracked reports/results/logs have a **32 MiB total budget**, with each
compressed shard <=512 KiB (also respecting CI's 1 MiB per-file limit). Track
compact per-row rewards, family/tier outcomes, mutation effects, retry/journal
metadata, summaries and the full 50-sample review packet in bounded compressed
shards. Full bulky rollouts stay under ignored artifacts/p3a/, with relative
paths, exact byte sizes and SHA256 hashes in committed manifests. Local compressed
raw storage budget is 2 GiB; exceeding either prospective budget stops further
launches and reports incomplete work, never drops existing evidence or weakens a
gate. Source scripts and manifests describe reconstruction/audit requirements;
unpublished local archives are not claimed available from GitHub.

Only phase-owned stopped containers may be cleaned up; frozen image, running
containers, other projects, images, networks and build caches must survive.
Inspect the frozen image before/after. If global docker system prune cannot be
limited to those stopped containers, use scoped container removal or report no
eligible cleanup; do not run a destructive global image/build-cache prune.

The final reports/P3a.md covers every criterion and measured value, per-family
and per-tier results, F3/F4/F6 separately, all failed design iterations,
interpretations, surprises, source/runtime/generator/image versions, storage,
project spend and local compute. A clean-context review and 50 author-reviewed
trajectories remain distinct from human labels. Commit/push reports and compact
results/manifests, delete P2B_PROMPT3.md at the end, update STATE and STOP. The
owner then chooses M1 packaging or E3; neither begins automatically.

## Implementation clarifications before freeze

The final prospective policy catalogue contains 32 controls: oracle, random,
twelve wrong policies, eight cheaters, shallow, find_0..3, near_1/near_2,
false_flag, never_report and report_only. The fresh population is therefore
8200 full v1 rollouts (2000 oracle plus 31*200 others). Design policy selection
uses ten primary design seeds per policy/tier, 1280 rollouts; sensitivity to
p=1,2,3 regrades the same immutable executions rather than repeating them.

Every family has correct intrinsic pipeline contexts. The additional removable
surface decoys are specifically the F1 purged training-label report and F2
full-history descriptive report; removing them uses equivalent live report
implementations, not zeros or dead statements. F3/F4/F5/F6 correct-context
surfaces occur in the necessary purge/identity/scheduling/selection stages,
which remain part of the clean research contract. Excluded folds remove the
held-out mutations and additional family-cued decoys, not the basic correct
research functionality. This is a synthetic-template separation, not a claim
that family concepts are statistically independent.

Signal formation and order scheduling are separate stages. A clean timestamped
signal is filled at the declared next close; the F5 same-bar scheduler wrongly
uses the next timestamp's already formed signal at that timestamp's close.
F1 instead changes information inside signal formation. Selection purges the
two-session fill/realization horizon. Evaluation witnesses exclude selection
observations. Admission requires the 0.05 floor for every required witness group,
not merely a change in an unused quantity. Future poisoning covers prices,
returns and fundamentals unavailable by the cutoff; listing/identifier fields
are retained. Real T3 joint and leave-one-out executions supplement the 1800
single-mutant executions before freeze.

Realization forms are direct expressions, operator-specific helper/control
expressions and comprehension/dataflow expressions. Presentation also refactors
zero-vector construction and square-root calculation independently of faults.
The public scripted auditor recognizes this restricted template grammar; its
success does not measure a general-purpose audit model. Design mutation bundles
run each script in its own Python subprocess, sharing a fresh checked container
within each seed. The fresh gate uses complete independent v1 rollouts with
fresh solver, primary, replay and poison containers and the shared retry policy.

### Random-control correction before any valid-random measurements

Independent clean review found the first development `random` solver was a
fixed invalid-output control, not a genuine random research proposal. Retain its
partial development run and label that limitation. Before measuring its
replacement, fix this restricted public-grammar distribution: each of the twelve
semantic faults is independently included with probability 1/2 (uniform over
all 4096 subsets, including clean with probability 1/4096); choose realization
uniformly from 0,1,2. Choose finding count uniformly from 0..8 inclusive; each
finding independently chooses one of six families and a source line uniformly
from all supplied script lines, with replacement. Seed the RNG from SHA256 of
canonical public input only. All patch proposals are executable research scripts;
this is not random invalid JSON and not a claim about random unrestricted Python.
The distribution, ten design primaries per policy/tier, grid and thresholds
remain fixed after its first execution. The corrected development iteration is
`p3a-policy-design-v2`; freeze must require its passing complete results. No
fresh gate or model baseline has run.

### 2026-10-28 — Retain seeds when some unplanted operators are inactive

Development v1 stopped on design replay seed1000776: none of32 candidate windows
made all twelve unrelated operators simultaneously effective. Its complete
candidate diagnostics are retained. Requiring all twelve on a clean replay was
an implementation constraint stronger than the owner's admitted-mutant rule.
Before rerunning affected studies, revise this case admission policy explicitly:
keep the requested seed, generator/config,96-session window and32-candidate cap;
prefer the first candidate where all twelve meet the same0.05 required-witness
floors. If none does, choose among those same32 candidates by maximum number of
eligible families, then eligible operators, then earliest candidate index. Mark
the selected candidate and retain every rejected operator/effect/reason. Only
operators meeting every required0.05 witness floor may be planted; T3 still
requires three distinct eligible families and every conditional effect>=0.05.
A nondegenerate clean case/replay needs no planted mutation. Never replace the
requested seed or call an inactive operator killed. Twelve wrong policies remain
unchanged; if an unplanted fault is inactive and outputs correct, the verifier
must credit those outputs and the wrong-policy aggregate may fail honestly.
If no valid T3 combination exists, retain all attempted combinations and fail.

This changes admission of research cases, not the frozen market generator,
seed partitions, thresholds, reward weights, exponent grid, financial semantics
or candidate cap. No fresh result has been seen. Both mutation and interaction
studies are repeated as v2 with distinct filenames; earlier source-bound v1
studies and the interrupted policy run remain available. The final policy study
is v2 and the frozen implementation must bind its exact semantic sources.

The selected exponent is recorded in the immutable committed freeze JSON. Design
rollout evidence stores scalar inputs, and all three grid candidates are checked
independently on those same records. The fresh gate loads the selected frozen
exponent into the trusted Task scorer before its first rollout; it is never set
from solver input. Selecting p=2/3 does not require rewriting source after the
source-bound design study. Any grid candidate may establish a passing design;
the smallest passing candidate is frozen.
