# Quant Research Integrity Environments

License: MIT

These environments test whether an agent can detect or avoid errors in quantitative research, including data leakage, unrealistic costs and false discoveries. All data are synthetic. Every reported number describes scripted verifier validation. No model results exist.

{{at_glance}}

## Motivation

Quantitative research can appear convincing while using future information, selecting a favorable universe, miscounting costs or ignoring multiple testing. This project aims to make integrity decisions verifiable against controlled synthetic ground truth rather than a model judge. The research question is whether reinforcement learning on such tasks can improve honest research behavior and transfer to unseen error families. That thesis is a plan, not an established result. [SPEC.md](SPEC.md) defines the research questions; [prereg.yaml](prereg.yaml) freezes the protocol and [AMENDMENTS.md](AMENDMENTS.md) records disclosed changes.

## Built and validated locally

The shared generator supplies latent factors, heavy-tailed returns, volatility regimes, report availability, restatements, corporate actions and stylized cost/capacity inputs. It has deterministic serialization and recorded development-seed diagnostics. The shared runtime uses fresh, inspected containers with no network, a read-only root, a single declared work mount, audited solver-UID commands and host-private grading. Generic or remote harness substitutions are refused.

E1 point-in-time backtesting, E5 cost realism and E6 data reconciliation passed their recorded numerical gates. These are scripted verifier tests, not language-model baselines. Extra oracle episodes support checker coverage; the per-tier policy tables below reproduce the frozen policy cells, each with **50 episodes per policy**, rather than implying that the extra oracle cohort is another random-policy sample. Wrong and cheater columns report the maximum individual policy mean, not an average that can hide a successful attack.

{{table:gates}}

Each result names its generator and frozen implementation. All numerical tables here use generator `{{generator_hash}}`. The E1/E5 gate freezes are embedded in their result files; the E6 gate records runtime `{{numeric_runtime_hash}}`. The current runtime correction is separately identified below, rather than relabeling historical gates.

## E2: leakage audit and mutation engine, built and validated

Given a synthetic research script and its public data/contract, identify planted bug families and source locations and submit an executable repair. T1 has a single obvious issue; T2 has one issue in a less direct realization; T3 combines three effective mutations from distinct families with distractors; T4 contains clean controls and behavior-preserving decoys. Reporting suspicious-looking clean code as faulty is penalized.

The engine uses one synthetic script template with **{{mutation_count}} mutations across {{family_count}} families**, each in **{{realization_count}} realizations**: F1 future-feature use and availability bypass; F2 global centering and scaling; F3 unpurged labels and selection overlap; F4 survivor filtering and ticker merging; F5 same-bar and submission-day fills; F6 test-set selection and uncorrected trial multiplicity. Realizations change surface form, not the financial error. Harmless F1/F2 report decoys preserve behavior. The [mutation design record](results/p3a_mutation_design_v3.json) retains mutation/decoy executions; the fresh [P3a3 gate](results/p3a3-gate.json) is the current E2 validation record.

The reward is a **weighted harmonic combination**. Let d be the F1 score for matched family and source location raised to the frozen exponent {{e2_exponent}}, p be functional patch quality, and c be clean-code quality. Stage reward is `1/(0.4/d + 0.4/p + 0.2/c)`, with zero if any component is zero. Dirty cases use c=1; clean cases use `c=(1+false_flags)^(-{{e2_exponent}})`. Numeric patch quality uses the same full/zero tolerance band described below. Each stage's error includes the poisoned-future prefix check, and the final reward is the lower primary/replay stage reward. Invalid schema, unsafe execution or tampering is a hard zero. See [reward source](envs/e2_leakage_audit/reward.py) and [phase report](reports/P3a3.md).

The clean-false-flag penalty is **soft**: an otherwise correct clean submission with an extra false finding still earns partial credit. The recorded T4 `false_flag` control mean is **{{e2_false_flag}}**. It is a diagnostic control, not part of the frozen worst-cheater roster; the clean false-positive gate measures oracle clean behavior. This limitation is retained openly.

### E2 synthetic verifier-validation results

These are scripted synthetic verifier-validation results, **not model performance**. The fresh gate completed **{{e2_rows}}** rollouts. Oracle cells contain 500 episodes per tier; other policy cells contain 50. Worst wrong is the maximum over the twelve individual wrong policies. Worst cheater is the maximum over the frozen constant-output, disabled-computation, canary, oracle-read, harness-tamper, network, schema-forgery and primary-only controls. Shallow detector is reported separately, with its predeclared ceiling applied separately to T2 and T3.

{{table:e2}}

Independent scalar-checker agreement is {{e2_checker}}, and oracle clean false-positive rate is {{e2_fp}}. The [independent actual-reward audit](results/p3a3_gate_audit.json) also checks the stored rewards, fresh-container provenance and replay routing. The fixed **{{e2_review_count}} author-reviewed trajectories** are recorded [separately](results/p3a3_author_review.json); these are not independent human labels. Frozen implementation: `{{e2_fresh_implementation}}`; runtime: `{{runtime_hash}}`; generator: `{{generator_hash}}`.

### E2 family coverage: other registered families

Counts are oracle episodes involving the family, not distinct templates or model trials. T3 episodes involve multiple families, so these counts overlap and must not be summed as disjoint episodes. Minimum planted effect is the recorded construction witness metric, not a treatment effect from a model study.

{{table:e2_families}}

### E2 family coverage: planned held-out families F3, F4, F6

These families are reserved for later leave-one-family-out training/evaluation. They are included here in synthetic verifier validation; this is **not a held-out model-transfer result**.

{{table:e2_heldout}}

### E2 development history and screen limitation

The first fresh gate failed on an infrastructure classification issue: a denied harness-tampering attempt was followed by a trusted Docker transfer timeout, and prior policy evidence prevented its infrastructure retry. Its underlying daemon-stall cause remains unknown. The fix completes recorded policy violations as hard zeros before unnecessary trusted transfer or replay, classifies typed host errors by their terminating operation, retains the bounded fresh-container retry and continues the planned schedule. A later transport-precedence correction was also retained and tested. Corrected implementation: `{{e2_implementation}}`.

Round-two stress then failed on a heavy-tail seed that cannot construct an E2 case under the unchanged price-return domain. Those failures were retained as admission failures, not relabelled as infrastructure; that round stopped before a new gate. P3a3 prospectively committed a deterministic construction-only screen before policy runs. It rejected **{{screen_rejected}} of {{screen_count}} design seeds** and **excludes extreme-tail episodes** that cannot build a case. The gate validates the screened population, not all draws of the frozen generator. See [the screen](results/p3a3_screen.json), [the prior failed prerequisite report](reports/P3a2.md) and [the passing P3a3 report](reports/P3a3.md).

<details>
<summary>Preserved historical failed-gate and round-two stress observations</summary>

These partial observations are not a pass of the original gate. Initial implementation: `{{first_e2_implementation}}`. The failed freeze and consumed marker remain unchanged; see [the first report](reports/P3a.md) and [completion audit](results/p3a_gate_audit.json).

{{table:e2_partial}}

The following stress runs failed their completion prerequisite. The [round-two gate-not-run record](results/p3a2_gate_not_run.json) belongs to that historical round, not to the later passing P3a3 gate.

{{table:e2_infrastructure}}

</details>

## E3: development prototype, design checks failed

A development prototype exists in [envs/e3_fdr_adjudication](envs/e3_fdr_adjudication). Its design checks failed in two rounds: the preflight contract was contradictory, and the round-two construction did not separate the controls. E3 is not validated or frozen. Both reports and their evidence are retained in [reports/P3b.md](reports/P3b.md).

## Planned work

A hosted-sandbox runtime backend is under consideration, not started, with unknown feasibility.

E4, the metered honest-null research loop, remains planned. Model baselines, evaluation freeze, leave-one-family-out training, GRPO and transfer studies are also planned. None is represented as a completed experiment. Model calls and GPU runs require the budget gate; sealed-test evaluation remains unavailable before its separate freeze. [Milestones](docs/MILESTONES.md) describe validation status and remaining research.

## Generator and data card

The [data card](docs/data_card.md) describes intended use, canonical bytes, seed partitions, oracle isolation, generating equations and limitations. Configured dimensions span {{ranges}}. These are synthetic draws, not calibration to market observations. The frozen generator version is `{{generator_hash}}`.

{{table:generator}}

The original factor-share screen did not pass every seed. The dated amendment changed that diagnostic to an across-seed median plus a per-seed floor, and the fresh cohort is reported separately. The data card retains the original diagnostic description; [AMENDMENTS.md](AMENDMENTS.md) and the fresh diagnostic result define the amended criterion. Earlier failed measurements were not rewritten. The fresh artifact retains legacy per-case flags from the original criterion; this table uses its recorded amended-check metrics and summary, not those legacy flags. Heavy tails can produce extreme or invalid price-return cases: the fresh diagnostic cohort recorded a maximum absolute one-day return of {{generator_tail}}, and the later E2 admission finding is a concrete downstream limit. Passing stylized-fact checks does not establish live-market realism.

## Validated tasksets and rewards

All rewards first reject invalid schema, unsafe execution or tampering. Submitted code runs inside checked containers; the host retains protected truth and scores actual execution records on primary and predictable fresh development data. There is no judge model and no accepted self-attested correctness flag. The definitions below describe the implemented rewards, whose detailed design is in the historical phase reports, not just the high-level preregistered weight labels.

### E1: point-in-time backtesting

Select the latest fundamental vintage actually available at a cutoff, honor revisions and active tradability, demean and gross-normalize a signal, and report its signal mean and next-day portfolio return. T1 supplies an explicit availability exercise; T2 obscures it among vintages and orderings; T3 combines availability, revisions and tradability with descriptive decoys; T4 presents valid future records and harmless ordering changes that must be filtered correctly, not accused of corruption.

Let q(e) be full quality inside the full-tolerance band, zero at the zero scale, and the decreasing cubic between them. With primary quality p and replay quality r, the implemented score is `0.8*p*r + 0.2*p*r*r`. Availability discipline is enforced through the causal financial oracle and separated cases, not a solver's declaration. See [reward source](envs/e1_pit_backtest/reward.py) and [gate report](reports/P2b2.md).

### E5: cost realism

Submit an actual gross weight path plus net-Sharpe and break-even-holding claims. The host applies capacity constraints, computes opening, turnover and closing costs, and recomputes financial metrics. T1 gives explicit cost conventions; T2 tests turnover and holding-period interpretation; T3 combines binding capacity and costs with descriptive decoys; T4 reverses asset order consistently and states correct units. Clipped capital is not silently reinvested.

Numeric errors cover claim consistency, oracle metrics and the submitted path. Let p and r be qualities of the maximum primary and replay errors. With primary Sharpe quality s and holding quality h, the score is `p*r*(0.5*s + 0.4*h + 0.1*r)`. See [reward source](envs/e5_cost_realism/reward.py), [financial definitions](envs/e5_cost_realism/finance.py) and [gate report](reports/P2c.md).

### E6: data traps

Reconcile stable listings, dated identifiers, active state, prices, adjusted prices and returns against independently supplied registry, audit and action records; identify planted quote anomalies. T1 plants a single corruption, T2 combines two, T3 combines the corruption families, and T4 is a clean control with legitimate actions and large-move decoys. Delistings must remain represented rather than being silently dropped.

Let u be numeric reconciliation quality. On dirty cases, anomaly quality a is the cube of anomaly-set F1; on clean cases it is the inverse cube of one plus the false-flag count. Stage reward is `min(u,a)*(0.6*u+0.4)`, and the episode takes the lower primary/replay stage reward. Thus exact reconstruction cannot compensate for missing anomalies, and accurate anomaly labels cannot compensate for bad reconstruction. See [reward source](envs/e6_data_traps/reward.py) and [revised design](reports/P2d3.md).

### Recorded reward sensitivity

These are recorded formula fixtures, not measured model difficulty or newly executed trials. E1 perturbs both reported fields on both executions. E5 perturbs both financial claims on both executions; it is a claim-consistency slice, not every possible path error. E6 uses exact anomaly flags with the same numeric error on both executions. The shared quality band is full through relative error `0.0001`, zero from `0.01`, and `1 - 3*u*u + 2*u*u*u` between, with `u=(error-0.0001)/0.0099`.

{{table:curves}}

E6 uses the revised sensitivity artifact, not the retired earlier high-exponent/coupled curve. The following detection slice assumes exact numeric reconstruction on both executions; clean-case F1 is not itself the reward definition.

{{table:e6_detection}}

## Validation protocol and results

Pre-registration freezes seed partitions, financial thresholds and held-out families. Dated amendments disclose prior observations rather than claiming that changes preceded results they actually followed. Source/image freezes precede one-shot gates; consumed markers and failed gates are retained. Development replay is deterministic and predictable, not a cryptographically sealed holdout. Sealed-test model evaluation is a separate, still-planned stage.

Validation tests and separate checker implementations precede verifier work, with independent AI review where recorded. These reviews are not independent human labels. Historical trajectory samples are labelled **author-reviewed** in their reports. P3a3 uses a new committed freeze and its fixed pre-freeze author-review selection; it does not replace the failed historical gate. Checker agreement validates the stated computation paths; it does not by itself establish empirical difficulty or financial external validity.

The early numeric gates taught that numeric self-attestation and batched execution were inadequate. Subsequent gates used actual submitted code, fresh containers and replay controls. E6's earlier anomaly scoring exposed nonzero rewards for conceptual wrong policies and overly steep near-miss suppression; its revision was disclosed and the later gate rerun without changing the generator or gate thresholds. The current E6 table uses that later gate. Consult [E1 history](reports/P2b2.md), [E5 history](reports/P2c.md), [E6 history](reports/P2d3.md) and the [amendment log](AMENDMENTS.md) for failures and exact source identities.

Retry classification follows the terminating trusted operation, not earlier policy evidence. The fixed allowance is at most one fresh whole-rollout retry for eligible infrastructure failure and at most 0.5% retries over the planned population. Complete policy-zero status does not excuse failed cleanup or unhealthy infrastructure. All planned initial attempts continue after a terminal row; no failed episode is removed to improve a gate mean.

## Recorded results

### Per-tier policy results

These are the frozen policy cells described above, with maxima over the full wrong and cheater rosters. Extra near controls retain their own names and are not silently folded into a passing cheater category.

**E1: point-in-time backtesting**

{{table:e1}}

**E5: cost realism**

{{table:e5}}

**E6: data traps**

{{table:e6}}

### Numerical-runtime stress

These historical passing numerical stress runs use runtime `{{numeric_runtime_hash}}`. The historical E2 stress table above records failed round-two runs. Later screened E2 stress and gate results are identified separately in the P3a3 validation record; these cohorts are not merged into a historical pass.

{{table:stress}}

### Determinism across runtime changes

The historical gate replay cohort and the later stratified corrected-runtime cohort are distinct. Current-runtime rows use an explicit seed list committed before reruns. Reward comparisons are exact, without a numerical tolerance. Independent audit also verified the later replay seeds in [the regression review](reports/P3a2_regression_review.md).

{{table:determinism}}

## Limitations

- In the frozen runtime used for the historical gates reported here, a solver or submitted program that exhausts the container's 32-process allowance produces an infrastructure failure (incomplete attempt), not a policy zero. The committed historical gate cheater and attack rosters contain no process-exhaustion attack ([roster review](results/p5b_historical_roster_review.json)); a later development-branch boundary batch exposed this failure. A narrow fix is under validation on a development branch.

- E2 uses **one synthetic script template with twelve mutations, each in three realizations**. Its scripted oracle demonstrates solvability within that template grammar, **not model performance** or general code-auditing ability.
- All data are synthetic; real-market validity is not established.
- Validation uses the project's checked local Docker execution. Hosted Hub and model-harness compatibility are not established.
- The independent E2 scalar checker consumes recorded execution errors; its agreement is not an independently implemented financial numerical oracle.
- [Hub architecture](reports/hub_architecture.md) explains why installing a taskset does not supply this project's host-private grading boundary, image or sandbox policy. Remote execution and model harnesses remain unsupported here.
- Replay seeds are predictable. They test functional consistency, not secrecy from a sufficiently informed adversary.
- Empirical model difficulty, transfer, training gains and model hack rates remain unmeasured. Scripted controls and admission/separation criteria can make a synthetic task easier or more selective than real research.
- E2 construction screening excludes extreme-tail episodes that cannot satisfy the unchanged price-return domain; its validation is conditional on admission. The [screen record](results/p3a3_screen.json) retains every rejected seed.
- The E2 clean false-flag penalty is soft: false accusations can retain substantial partial reward even when the repair is functionally exact. Oracle clean false-positive success does not establish zero reward for every false-flag policy.
- Heavy tails, restricted corporate-action patterns and simplified costs limit realism. A passing numerical gate does not imply profitable or safe investment decisions.
- Full raw trajectories and journals are retained locally behind committed hash manifests; GitHub contains bounded summaries and selected full failure packets. Frozen historical results are not automatically relabelled after a source or documentation change.

## Reproduction

{{versions}}

Install the locked project and regenerate documentation without running a gate:

```bash
uv sync --frozen
uv run python scripts/reproduce_table.py --check
uv run python scripts/reproduce_table.py --table e1
uv run python scripts/reproduce_table.py --write
uv run pytest tests/test_readme_tables.py
```

The template is [docs/README.template.md](docs/README.template.md). Every README table has a named renderer in [scripts/reproduce_table.py](scripts/reproduce_table.py). The check compares the complete README, including narrative numbers, against its source-backed rendering; tests deliberately alter displayed numbers and source values to verify rejection. Recorded means are displayed to six decimals, while exact source values remain in JSON. Tables use stored artifacts only; rendering does not execute a solver or create a new metric.

For existing integration tests, Docker Engine and the project-specific work/private directories described in [COMPAT.md](COMPAT.md) are required. The recorded immutable validated image is `{{image_hash}}`. The [Dockerfile](envs/e1_pit_backtest/container/Dockerfile) pins its base image and strace package. A new build can have a different image ID; it must not be presented as the recorded frozen image or silently substituted into historical evidence.

```bash
docker image inspect {{image_hash}} --format '{{.Id}}'
QI_REAL_SANDBOX=1 uv run pytest
uv run eval @ configs/e1_scripted.toml --no-serve --no-rich --no-push
uv run eval @ configs/e5_scripted.toml --no-serve --no-rich --no-push
```

The CLI examples use development configs and the scripted no-model harness, never a hosted service. Standard tests can exercise the checked boundary; do not rerun a consumed one-shot gate to reproduce a table. Read-only rendering is the intended route to these recorded results. See [validation milestones](docs/MILESTONES.md) and the [source-backed resume draft](docs/resume_bullets.md).
