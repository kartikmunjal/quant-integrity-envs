# Quant Research Integrity Environments

## At a glance

- Synthetic quantitative research-integrity tasksets with deterministic verifiers.
- Validated locally: generator, checked runtime and E1/E5/E6 across **4 tiers**; **21,800** scripted numerical-gate rollouts.
- Corrected-runtime regression: **3,000** exact reward matches.
- E2: the first gate failed on infrastructure classification; a fix is implemented, and a separate case-admission problem on heavy-tail seeds was found.
- Planned: E3, E4, model baselines, training and transfer studies.
- No model results are claimed.

A synthetic testbed for quantitative research integrity, with deterministic financial verifiers and checked local Docker execution. The generator, shared runtime and numerical tasksets E1, E5 and E6 have recorded scripted validation. The mutation engine and E2 are implemented but not yet validated: their first fresh gate failed and remains incomplete, and the infrastructure correction's design stress still fails case admission. E3, E4, model baselines and training are planned. No model-performance, real-market or hosted-Hub result is claimed.

## Motivation

Quantitative research can appear convincing while using future information, selecting a favorable universe, miscounting costs or ignoring multiple testing. This project aims to make integrity decisions verifiable against controlled synthetic ground truth rather than a model judge. The research question is whether reinforcement learning on such tasks can improve honest research behavior and transfer to unseen error families. That thesis is a plan, not an established result. [SPEC.md](SPEC.md) defines the research questions; [prereg.yaml](prereg.yaml) freezes the protocol and [AMENDMENTS.md](AMENDMENTS.md) records disclosed changes.

## Built and validated locally

The shared generator supplies latent factors, heavy-tailed returns, volatility regimes, report availability, restatements, corporate actions and stylized cost/capacity inputs. It has deterministic serialization and recorded development-seed diagnostics. The shared runtime uses fresh, inspected containers with no network, a read-only root, a single declared work mount, audited solver-UID commands and host-private grading. Generic or remote harness substitutions are refused.

E1 point-in-time backtesting, E5 cost realism and E6 data reconciliation passed their recorded numerical gates. These are scripted verifier tests, not language-model baselines. Extra oracle episodes support checker coverage; the per-tier policy tables below reproduce the frozen policy cells, each with **50 episodes per policy**, rather than implying that the extra oracle cohort is another random-policy sample. Wrong and cheater columns report the maximum individual policy mean, not an average that can hide a successful attack.

<!-- table:gates -->
| Environment | Gate rollouts | Real checker comparisons | Agreement | Clean oracle flags (policy cell) | Gate |
|---|---|---|---|---|---|
| E1 | 6,400 | 6,400 | 1.000000 | 0 / 50 | PASS |
| E5 | 7,000 | 7,000 | 1.000000 | 0 / 50 | PASS |
| E6 | 8,400 | 8,400 | 1.000000 | 0 / 50 | PASS |

Sources: [p2b2_gate.json](results/p2b2_gate.json), [p2c_gate.json](results/p2c_gate.json), [p2d3-gate-E6-c12.json](results/p2d3-gate-E6-c12.json).
<!-- /table:gates -->

Each result names its generator and frozen implementation. All numerical tables here use generator `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`. The E1/E5 gate freezes are embedded in their result files; the E6 gate records runtime `5ac8cf100aabc4d4b47f38fe8ecc4a34fe4db1c77f6042d719c165489769781a`. The current runtime correction is separately identified below, rather than relabeling historical gates.

## Implemented but not yet validated: mutation engine and E2

The mutation engine and E2 (`qi-leakage-audit`) are implemented. Their first fresh gate **failed and remains incomplete** following an infrastructure classification issue: a denied harness-tampering attempt was followed by a Docker host timeout during submission transfer. The frozen classification rule treated the collision as terminal policy evidence, so no retry occurred. The underlying host-stall cause is unknown.

These are **partial gate observations, not a gate pass**:

<!-- table:e2_partial -->
| Partial observation | Recorded result |
|---|---|
| Planned rollouts | 8,200 |
| Completed rollouts | 5,657 |
| Terminal failures | 1 |
| Unexecuted rollouts | 2,542 |
| Retries | 0 |
| Scripted oracle mean reward | 1.000000 in each tier; 500 completed per tier |
| Random mean reward | 0.000000 in each tier; 50 completed per tier |
| Largest conceptual wrong-policy mean | 0.020000; all 12 policies completed 50 cases per tier |
| Clean oracle false-positive rate | 0 / 500 |
| Independent scalar-checker agreement | 1.000000 on 5,657 completed records |

Sources: [p3a-gate.json](results/p3a-gate.json).
<!-- /table:e2_partial -->

Later fresh controls, including the shallow detector, were not reached. Passing observed cells does not establish completion or overall validation. The failed gate, its freeze and consumed marker remain historical evidence. Source: [first phase report](reports/P3a.md), [completion audit](results/p3a_gate_audit.json), and [independent post-gate review](reports/P3a_gate_review.md). Initial frozen implementation: `d0eecc88b005d14ddec3a6a2f09a22881fb35e8c`.

The infrastructure fix is now implemented and tested: recorded policy violations close as complete hard zeros before trusted result transfer or replay; typed terminating host errors retain their bounded whole-rollout retry; terminal rows no longer stop the remaining schedule. A later fault-injection finding corrected transport-status precedence, and both stress runs were repeated against that corrected source. Corrected implementation: `aa86c69801a07c8aaf627a6336503235e90e9fdf`; runtime: `fad402d113ca9e19f082ac45e3e0904edb128b9e672c351fe3a2d62eb699a827`.

<!-- table:e2_infrastructure -->
| Concurrency | Rows recorded | Complete | Admission failures | Host timeouts | Retries | Stress |
|---|---|---|---|---|---|---|
| 8 | 5,000 | 4,951 | 49 | 0 | 0 | FAIL |
| 12 | 5,000 | 4,951 | 49 | 0 | 0 | FAIL |

Sources: [p3a2-r2-stress-c8.json](results/p3a2-r2-stress-c8.json), [p3a2-r2-stress-c12.json](results/p3a2-r2-stress-c12.json).
<!-- /table:e2_infrastructure -->

The unchanged design seed's price-return domain rejection reproduces without Docker. Failures were retained, not replaced or reclassified as infrastructure. The source-bound stress prerequisite therefore failed. No new freeze or fresh gate was consumed, and no new shallow-detector result or author-reviewed gate sample exists. See [the failed prerequisite report](reports/P3a2.md), [the independent stress audit](reports/P3a2_r2_stress_audit.md) and [the explicit gate-not-run record](results/p3a2_gate_not_run.json). M0 packaging is the current target; M1 has not been reached.

## Planned work

A hosted-sandbox runtime backend is under consideration, not started, with unknown feasibility.

E3 multiple-testing adjudication and E4 the metered honest-null research loop are planned. Model baselines, evaluation freeze, leave-one-family-out training, GRPO and transfer studies are also planned. None is represented as a completed experiment. Model calls and GPU runs require the budget gate and the relevant owner authorization; sealed-test evaluation remains unavailable before its separate freeze. [Milestones](docs/MILESTONES.md) distinguish packaging from validated research and release readiness.

## Generator and data card

The [data card](docs/data_card.md) describes intended use, canonical bytes, seed partitions, oracle isolation, generating equations and limitations. Configured dimensions span 200 to 1000 assets and 500 to 1500 sessions. These are synthetic draws, not calibration to market observations. The frozen generator version is `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.

<!-- table:generator -->
| Cohort | Dev seeds | Per-seed passes | Per-seed failures | Factor criterion |
|---|---|---|---|---|
| Initial diagnostic | 5 | 5 | 0 | per-seed factor share >= 0.30 |
| Original per-seed screen | 200 | 167 | 33 | per-seed factor share >= 0.30 |
| Fresh amended-criterion cohort | 200 | 200 | 0 | median factor share >= 0.30; per-seed floor >= 0.15 |

Sources: [p1_diagnostics.json](results/p1_diagnostics.json), [p1_addendum_diagnostics.json](results/p1_addendum_diagnostics.json), [p1_followup_fresh_diagnostics.json](results/p1_followup_fresh_diagnostics.json).
<!-- /table:generator -->

The original factor-share screen did not pass every seed. The dated amendment changed that diagnostic to an across-seed median plus a per-seed floor, and the fresh cohort is reported separately. The data card retains the original diagnostic description; [AMENDMENTS.md](AMENDMENTS.md) and the fresh diagnostic result define the amended criterion. Earlier failed measurements were not rewritten. The fresh artifact retains legacy per-case flags from the original criterion; this table uses its recorded amended-check metrics and summary, not those legacy flags. Heavy tails can produce extreme or invalid price-return cases: the fresh diagnostic cohort recorded a maximum absolute one-day return of 3.463940, and the later E2 admission finding is a concrete downstream limit. Passing stylized-fact checks does not establish live-market realism.

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

<!-- table:curves -->
| Relative error | Single numeric quality | E1: both fields, both executions | E5: both claims, both executions | E6: numeric error, exact flags |
|---|---|---|---|---|
| 0.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| 0.000100 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| 0.001000 | 0.976709 | 0.949517 | 0.931742 | 0.963060 |
| 0.002575 | 0.843750 | 0.689667 | 0.600677 | 0.764648 |
| 0.005050 | 0.500000 | 0.225000 | 0.125000 | 0.350000 |
| 0.007525 | 0.156250 | 0.020294 | 0.003815 | 0.077148 |
| 0.010000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 0.020000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |

Sources: [p2d2_reward_sensitivity.json](results/p2d2_reward_sensitivity.json), [p2d2_revision_sensitivity.json](results/p2d2_revision_sensitivity.json).
<!-- /table:curves -->

E6 uses the revised sensitivity artifact, not the retired earlier high-exponent/coupled curve. The following detection slice assumes exact numeric reconstruction on both executions; clean-case F1 is not itself the reward definition.

<!-- table:e6_detection -->
| True anomalies | Found | False flags | F1 | Reward with exact numeric output |
|---|---|---|---|---|
| 0 | 0 | 0 | 1.000000 | 1.000000 |
| 0 | 0 | 1 | 0.000000 | 0.125000 |
| 0 | 0 | 2 | 0.000000 | 0.037037 |
| 6 | 0 | 0 | 0.000000 | 0.000000 |
| 6 | 1 | 0 | 0.285714 | 0.023324 |
| 6 | 3 | 0 | 0.666667 | 0.296296 |
| 6 | 5 | 0 | 0.909091 | 0.751315 |
| 6 | 6 | 0 | 1.000000 | 1.000000 |

Sources: [p2d2_revision_sensitivity.json](results/p2d2_revision_sensitivity.json).
<!-- /table:e6_detection -->

## Validation protocol and results

Pre-registration freezes seed partitions, financial thresholds and held-out families. Dated amendments disclose prior observations rather than claiming that changes preceded results they actually followed. Source/image freezes precede one-shot gates; consumed markers and failed gates are retained. Development replay is deterministic and predictable, not a cryptographically sealed holdout. Sealed-test model evaluation is a separate, still-planned stage.

Validation tests and separate checker implementations precede verifier work, with independent AI review where recorded. These reviews are not independent human labels. Historical trajectory samples are labelled **author-reviewed** in their reports. The current E2 fresh gate has no replacement or retrospective sample. Checker agreement validates the stated computation paths; it does not by itself establish empirical difficulty or financial external validity.

The early numeric gates taught that numeric self-attestation and batched execution were inadequate. Subsequent gates used actual submitted code, fresh containers and replay controls. E6's earlier anomaly scoring exposed nonzero rewards for conceptual wrong policies and overly steep near-miss suppression; its revision was disclosed and the later gate rerun without changing the generator or gate thresholds. The current E6 table uses that later gate. Consult [E1 history](reports/P2b2.md), [E5 history](reports/P2c.md), [E6 history](reports/P2d3.md) and the [amendment log](AMENDMENTS.md) for failures and exact source identities.

Retry classification follows the terminating trusted operation, not earlier policy evidence. The fixed allowance is at most one fresh whole-rollout retry for eligible infrastructure failure and at most 0.5% retries over the planned population. Complete policy-zero status does not excuse failed cleanup or unhealthy infrastructure. All planned initial attempts continue after a terminal row; no failed episode is removed to improve a gate mean.

## Recorded results

### Per-tier policy results

These are the frozen policy cells described above, with maxima over the full wrong and cheater rosters. Extra near controls retain their own names and are not silently folded into a passing cheater category.

**E1: point-in-time backtesting**

<!-- table:e1 -->
| Tier | Oracle | Random | Worst wrong (10 policies) | Worst cheater (10 policies) | near_miss |
|---|---|---|---|---|---|
| T1 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.225000 |
| T2 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.225000 |
| T3 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.225000 |
| T4 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.225000 |

Sources: [p2b2_gate.json](results/p2b2_gate.json).
<!-- /table:e1 -->

**E5: cost realism**

<!-- table:e5 -->
| Tier | Oracle | Random | Worst wrong (12 policies) | Worst cheater (10 policies) | near_miss | near_sharpe_only |
|---|---|---|---|---|---|---|
| T1 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.125000 | 0.175000 |
| T2 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.125000 | 0.175000 |
| T3 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.125000 | 0.175000 |
| T4 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.125000 | 0.175000 |

Sources: [p2c_gate.json](results/p2c_gate.json).
<!-- /table:e5 -->

**E6: data traps**

<!-- table:e6 -->
| Tier | Oracle | Random | Worst wrong (10 policies) | Worst cheater (10 policies) | near_miss | near_small | near_false_flag |
|---|---|---|---|---|---|---|---|
| T1 | 1.000000 | 0.000000 | 0.002761 | 0.000000 | 0.350000 | 0.764648 | 0.296296 |
| T2 | 1.000000 | 0.000000 | 0.005788 | 0.000000 | 0.350000 | 0.764648 | 0.512000 |
| T3 | 1.000000 | 0.000000 | 0.034114 | 0.000000 | 0.350000 | 0.764648 | 0.786527 |
| T4 | 1.000000 | 0.000000 | 0.006796 | 0.000000 | 0.350000 | 0.764648 | 0.125000 |

Sources: [p2d3-gate-E6-c12.json](results/p2d3-gate-E6-c12.json).
<!-- /table:e6 -->

### Numerical-runtime stress

These historical passing numerical stress runs use runtime `5ac8cf100aabc4d4b47f38fe8ecc4a34fe4db1c77f6042d719c165489769781a`. The separate E2 stress table above uses the corrected runtime and remains failed; these cohorts are not merged into a passing result.

<!-- table:stress -->
| Environment | Concurrency | Planned | Complete | Terminal failures | Retries | Stress |
|---|---|---|---|---|---|---|
| E1 | 12 | 5,000 | 5,000 | 0 | 0 | PASS |
| E1 | 24 | 5,000 | 5,000 | 0 | 0 | PASS |
| E5 | 12 | 5,000 | 5,000 | 0 | 0 | PASS |
| E5 | 24 | 5,000 | 5,000 | 0 | 0 | PASS |
| E6 | 12 | 5,000 | 5,000 | 0 | 0 | PASS |
| E6 | 24 | 5,000 | 5,000 | 0 | 0 | PASS |

Sources: [p2d3-r2-stress-E1-c12.json](results/p2d3-r2-stress-E1-c12.json), [p2d3-r2-stress-E1-c24.json](results/p2d3-r2-stress-E1-c24.json), [p2d3-r2-stress-E5-c12.json](results/p2d3-r2-stress-E5-c12.json), [p2d3-r2-stress-E5-c24.json](results/p2d3-r2-stress-E5-c24.json), [p2d3-r2-stress-E6-c12.json](results/p2d3-r2-stress-E6-c12.json), [p2d3-r2-stress-E6-c24.json](results/p2d3-r2-stress-E6-c24.json).
<!-- /table:stress -->

### Determinism across runtime changes

The historical gate replay cohort and the later stratified corrected-runtime cohort are distinct. Current-runtime rows use an explicit seed list committed before reruns. Reward comparisons are exact, without a numerical tolerance. Independent audit also verified the later replay seeds in [the regression review](reports/P3a2_regression_review.md).

<!-- table:determinism -->
| Cohort | Environment | Rows | Reward differences | Replay-seed differences | Regression |
|---|---|---|---|---|---|
| Historical gate replay | E1 | 6,400 | 0 | 0 | PASS |
| Historical gate replay | E5 | 7,000 | 0 | 0 | PASS |
| Historical gate replay | E6 | 7,000 | 0 | 0 | PASS |
| Corrected shared runtime | E1 | 1,000 | 0 | see independent audit | PASS |
| Corrected shared runtime | E5 | 1,000 | 0 | see independent audit | PASS |
| Corrected shared runtime | E6 | 1,000 | 0 | see independent audit | PASS |

Sources: [p2d3-r2-determinism-E1-c24.json](results/p2d3-r2-determinism-E1-c24.json), [p2d3-r2-determinism-E5-c24.json](results/p2d3-r2-determinism-E5-c24.json), [p2d3-r2-determinism-E6-c24.json](results/p2d3-r2-determinism-E6-c24.json), [p3a2-regression-e1.json](results/p3a2-regression-e1.json), [p3a2-regression-e5.json](results/p3a2-regression-e5.json), [p3a2-regression-e6.json](results/p3a2-regression-e6.json).
<!-- /table:determinism -->

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

Python `>=3.11,<3.15`; `verifiers==0.3.1`, pinned in [uv.lock](uv.lock).

Install the locked project and regenerate documentation without running a gate:

```bash
uv sync --frozen
uv run python scripts/reproduce_table.py --check
uv run python scripts/reproduce_table.py --table e1
uv run python scripts/reproduce_table.py --write
uv run pytest tests/test_readme_tables.py
```

The template is [docs/README.template.md](docs/README.template.md). Every README table has a named renderer in [scripts/reproduce_table.py](scripts/reproduce_table.py). The check compares the complete README, including narrative numbers, against its source-backed rendering; tests deliberately alter displayed numbers and source values to verify rejection. Recorded means are displayed to six decimals, while exact source values remain in JSON. Tables use stored artifacts only; rendering does not execute a solver or create a new metric.

For existing integration tests, Docker Engine and the owner-authorized project work/private directories described in [COMPAT.md](COMPAT.md) are required. The recorded immutable validated image is `sha256:9cc803aaddbbb1a17c9eef928b5438d61769c9c9ba928fc285bc7ee622ad8353`. The [Dockerfile](envs/e1_pit_backtest/container/Dockerfile) pins its base image and strace package. A new build can have a different image ID; it must not be presented as the recorded frozen image or silently substituted into historical evidence.

```bash
docker image inspect sha256:9cc803aaddbbb1a17c9eef928b5438d61769c9c9ba928fc285bc7ee622ad8353 --format '{{.Id}}'
QI_REAL_SANDBOX=1 uv run pytest
uv run eval @ configs/e1_scripted.toml --no-serve --no-rich --no-push
uv run eval @ configs/e5_scripted.toml --no-serve --no-rich --no-push
```

The CLI examples use development configs and the scripted no-model harness, never a hosted service. Standard tests can exercise the checked boundary; do not rerun a consumed one-shot gate to reproduce a table. Read-only rendering is the intended route to these recorded results. The owner runs release review; this packaging step claims no release-review pass, adds no license, changes no repository identity or visibility, and publishes no package or Hub environment. See [M0 and later milestones](docs/MILESTONES.md) and the [source-backed resume draft](docs/resume_bullets.md).
