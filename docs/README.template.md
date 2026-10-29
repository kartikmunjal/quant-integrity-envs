# Quant Research Integrity Environments

A synthetic testbed for quantitative research integrity, with deterministic financial verifiers and checked local Docker execution. The generator, shared runtime and numerical tasksets E1, E5 and E6 have recorded scripted validation. The mutation engine and E2 are implemented but not yet validated: their first fresh gate failed and remains incomplete, and the infrastructure correction's design stress still fails case admission. E3, E4, model baselines and training are planned. No model-performance, real-market or hosted-Hub result is claimed.

## Motivation

Quantitative research can appear convincing while using future information, selecting a favorable universe, miscounting costs or ignoring multiple testing. This project aims to make integrity decisions verifiable against controlled synthetic ground truth rather than a model judge. The research question is whether reinforcement learning on such tasks can improve honest research behavior and transfer to unseen error families. That thesis is a plan, not an established result. [SPEC.md](SPEC.md) defines the research questions; [prereg.yaml](prereg.yaml) freezes the protocol and [AMENDMENTS.md](AMENDMENTS.md) records disclosed changes.

## Built and validated locally

The shared generator supplies latent factors, heavy-tailed returns, volatility regimes, report availability, restatements, corporate actions and stylized cost/capacity inputs. It has deterministic serialization and recorded development-seed diagnostics. The shared runtime uses fresh, inspected containers with no network, a read-only root, a single declared work mount, audited solver-UID commands and host-private grading. Generic or remote harness substitutions are refused.

E1 point-in-time backtesting, E5 cost realism and E6 data reconciliation passed their recorded numerical gates. These are scripted verifier tests, not language-model baselines. Extra oracle episodes support checker coverage; the per-tier policy tables below reproduce the frozen policy cells, each with **50 episodes per policy**, rather than implying that the extra oracle cohort is another random-policy sample. Wrong and cheater columns report the maximum individual policy mean, not an average that can hide a successful attack.

{{table:gates}}

Each result names its generator and frozen implementation. All numerical tables here use generator `{{generator_hash}}`. The E1/E5 gate freezes are embedded in their result files; the E6 gate records runtime `{{numeric_runtime_hash}}`. The current runtime correction is separately identified below, rather than relabeling historical gates.

## Implemented but not yet validated: mutation engine and E2

The mutation engine and E2 (`qi-leakage-audit`) are implemented. Their first fresh gate **failed and remains incomplete** following an infrastructure classification issue: a denied harness-tampering attempt was followed by a Docker host timeout during submission transfer. The frozen classification rule treated the collision as terminal policy evidence, so no retry occurred. The underlying host-stall cause is unknown.

These are **partial gate observations, not a gate pass**:

{{table:e2_partial}}

Later fresh controls, including the shallow detector, were not reached. Passing observed cells does not establish completion or overall validation. The failed gate, its freeze and consumed marker remain historical evidence. Source: [first phase report](reports/P3a.md), [completion audit](results/p3a_gate_audit.json), and [independent post-gate review](reports/P3a_gate_review.md). Initial frozen implementation: `{{first_e2_implementation}}`.

The infrastructure fix is now implemented and tested: recorded policy violations close as complete hard zeros before trusted result transfer or replay; typed terminating host errors retain their bounded whole-rollout retry; terminal rows no longer stop the remaining schedule. A later fault-injection finding corrected transport-status precedence, and both stress runs were repeated against that corrected source. Corrected implementation: `{{e2_implementation}}`; runtime: `{{runtime_hash}}`.

{{table:e2_infrastructure}}

The unchanged design seed's price-return domain rejection reproduces without Docker. Failures were retained, not replaced or reclassified as infrastructure. The source-bound stress prerequisite therefore failed. No new freeze or fresh gate was consumed, and no new shallow-detector result or author-reviewed gate sample exists. See [the failed prerequisite report](reports/P3a2.md), [the independent stress audit](reports/P3a2_r2_stress_audit.md) and [the explicit gate-not-run record](results/p3a2_gate_not_run.json). M0 packaging is the current target; M1 has not been reached.

## Planned work

E3 multiple-testing adjudication and E4 the metered honest-null research loop are planned. Model baselines, evaluation freeze, leave-one-family-out training, GRPO and transfer studies are also planned. None is represented as a completed experiment. Model calls and GPU runs require the budget gate and the relevant owner authorization; sealed-test evaluation remains unavailable before its separate freeze. [Milestones](docs/MILESTONES.md) distinguish packaging from validated research and release readiness.

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

Validation tests and separate checker implementations precede verifier work, with independent AI review where recorded. These reviews are not independent human labels. Historical trajectory samples are labelled **author-reviewed** in their reports. The current E2 fresh gate has no replacement or retrospective sample. Checker agreement validates the stated computation paths; it does not by itself establish empirical difficulty or financial external validity.

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

These historical passing numerical stress runs use runtime `{{numeric_runtime_hash}}`. The separate E2 stress table above uses the corrected runtime and remains failed; these cohorts are not merged into a passing result.

{{table:stress}}

### Determinism across runtime changes

The historical gate replay cohort and the later stratified corrected-runtime cohort are distinct. Current-runtime rows use an explicit seed list committed before reruns. Reward comparisons are exact, without a numerical tolerance. Independent audit also verified the later replay seeds in [the regression review](reports/P3a2_regression_review.md).

{{table:determinism}}

## Limitations

- E2 uses **one synthetic script template with twelve mutations, each in three realizations**. Its scripted oracle demonstrates solvability within that template grammar, **not model performance** or general code-auditing ability.
- All data are synthetic; real-market validity is not established.
- Validation uses the project's checked local Docker execution. Hosted Hub and model-harness compatibility are not established.
- The independent E2 scalar checker consumes recorded execution errors; its agreement is not an independently implemented financial numerical oracle.
- [Hub architecture](reports/hub_architecture.md) explains why installing a taskset does not supply this project's host-private grading boundary, image or sandbox policy. Remote execution and model harnesses remain unsupported here.
- Replay seeds are predictable. They test functional consistency, not secrecy from a sufficiently informed adversary.
- Empirical model difficulty, transfer, training gains and model hack rates remain unmeasured. Scripted controls and admission/separation criteria can make a synthetic task easier or more selective than real research.
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

For existing integration tests, Docker Engine and the owner-authorized project work/private directories described in [COMPAT.md](COMPAT.md) are required. The recorded immutable validated image is `{{image_hash}}`. The [Dockerfile](envs/e1_pit_backtest/container/Dockerfile) pins its base image and strace package. A new build can have a different image ID; it must not be presented as the recorded frozen image or silently substituted into historical evidence.

```bash
docker image inspect {{image_hash}} --format '{{.Id}}'
QI_REAL_SANDBOX=1 uv run pytest
uv run eval @ configs/e1_scripted.toml --no-serve --no-rich --no-push
uv run eval @ configs/e5_scripted.toml --no-serve --no-rich --no-push
```

The CLI examples use development configs and the scripted no-model harness, never a hosted service. Standard tests can exercise the checked boundary; do not rerun a consumed one-shot gate to reproduce a table. Read-only rendering is the intended route to these recorded results. The owner runs release review; this packaging step claims no release-review pass, adds no license, changes no repository identity or visibility, and publishes no package or Hub environment. See [M0 and later milestones](docs/MILESTONES.md) and the [source-backed resume draft](docs/resume_bullets.md).
