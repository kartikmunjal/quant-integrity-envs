# Compatibility note

Checked against official upstream documentation and source on 2026-10-21. These pins are the P0 integration target; changes require an explicit compatibility review.

## Pins

- Python: `>=3.11,<3.15` (CI uses 3.11).
- `verifiers==0.3.1`, tag commit `b2e4e8157783b2c0dffc7821044c87f29f1c3ccf`.
- `prime-rl` commit `477d438193e77df3a45edab58e478fad3cde32df` for the Phase 6 training workspace. It is pinned by commit because the official training path is a source checkout with submodules, not a dependency of this environment package.
- Phase 6 base model: `PrimeIntellect/Qwen3-1.7B`. This is the smallest model in the preregistered 1.5B–3B interval shown in an official prime-rl multi-turn RL example. The upstream Wordle guide describes it as a clone of `Qwen/Qwen3-1.7B` with a chat template suitable for multi-turn RL.

Project dependencies are pinned in `pyproject.toml`; the installation set is pinned in `uv.lock`.

## Verifiers v1 structure

In v1, the Hub unit is a **taskset**, not a monolithic legacy environment. A `Taskset[TaskT, ConfigT]` loads serializable `TaskData` rows and task behavior. A task supplies lifecycle hooks, tools, metrics, and deterministic rewards using decorators such as `@vf.metric` and `@vf.reward`. An `Env` controls one or more agents and produces an `Episode`; for this project, the standard fallback is `SingleAgentEnv`; protected E1 execution uses the project-specific checked `E1Env`. The pinned wheel does not export `IsolatedVerifierEnv`.

The numeric integrity environments will therefore be packaged as tasksets. Each will contain:

1. deterministic synthetic task construction and declared agent-visible artifacts;
2. an agent harness and container runtime with network disabled;
3. task tools and output schema;
4. deterministic metrics/rewards, with no model judge;
5. declared result artifacts transferred to an isolated verifier runtime; and
6. local validation fixtures and a Hub package manifest.

Official references:

- [Verifiers v1 overview](https://github.com/PrimeIntellect-ai/verifiers/blob/v0.3.1/docs/v1/overview.md)
- [Verifiers v1 environment control flow and isolated verification](https://github.com/PrimeIntellect-ai/verifiers/blob/v0.3.1/docs/v1/env.md)
- [Verifiers v1 evaluation](https://github.com/PrimeIntellect-ai/verifiers/blob/v0.3.1/docs/v1/evaluation.md)

## Sandboxes, isolation, and rewards

The installed pinned v1 API has no `IsolatedVerifierEnv`. E1 uses a custom
`E1Env` which provisions an inspected `E1Runtime`, then delegates to the ordinary
v1 agent rollout. Finalization transfers only bounded regular source bytes and
destroys that solver container. Scoring re-executes those bytes in separate
primary and fresh-seed containers. Protected oracle data stays on the host,
never inside any solver container. These are project controls; they are not
promises supplied by a nonexistent upstream environment class.

The current v1 API describes decorated deterministic rewards and metrics rather than the legacy rubric abstraction. Project reward weights from `prereg.yaml` will be composed as deterministic `@vf.reward` outputs. Hard gates are checked before weighted terms. No model-backed judge is configured.

Canary reads and harness mutation are runtime evidence recorded outside agent-writable artifacts. E1 oracle material stays in the protected host verifier; it is never staged into a solver or replay runtime. Phase implementations must verify these assumptions against the pinned runtime with integration tests.

## Publishing and local evaluation

The official CLI flow is:

- scaffold/validate locally with the installed v1 tools and use `eval` for v1 tasksets;
- keep v1 evaluation local with `eval ... --no-push` during development; `vf-eval` is the legacy entry point in this wheel;
- install a Hub package with `prime env install <environment-name>`; and
- publish only after P7 owner approval with `prime env push <environment-name>`.

No package is published in P0.

Official reference: [Prime CLI repository](https://github.com/PrimeIntellect-ai/prime#environments).

## GRPO and LoRA path

The pinned `prime-rl` path uses `uv run rl @ <config.toml>`. GRPO is the default RL algorithm and may be selected explicitly with `orchestrator.train.algo.type = "grpo"`. LoRA is enabled under `[trainer.model.lora]` with rank, alpha, dropout, and optional target modules. Upstream states that LoRA works for RL; its weight transport falls back from NCCL to filesystem. The model is served through prime-rl's inference entrypoint so live adapter updates are supported.

Official references:

- [prime-rl training](https://github.com/PrimeIntellect-ai/prime-rl/blob/477d438193e77df3a45edab58e478fad3cde32df/docs/training.md)
- [prime-rl LoRA documentation](https://github.com/PrimeIntellect-ai/prime-rl/blob/477d438193e77df3a45edab58e478fad3cde32df/docs/advanced.md#lora-training)
- [prime-rl Wordle model example](https://github.com/PrimeIntellect-ai/prime-rl/tree/477d438193e77df3a45edab58e478fad3cde32df/examples/basic/wordle)

## SPEC mismatches and decisions

1. **Rubric terminology:** SPEC says “rubrics,” while Verifiers v1 uses task-level decorated metrics/rewards for deterministic scoring. Decision: implement preregistered reward terms as deterministic rewards, not an agentic/model judge.
2. **Environment packaging:** SPEC speaks of six environments; the current Hub exposes user-created tasksets paired with an `Env` control-flow implementation. Decision: use taskset packages with explicit control flow; E1 selects the project-specific checked `E1Env`. No nonexistent upstream isolated-verifier class is assumed.
3. **Sandbox sufficiency:** a plain subprocess runtime is not a sufficient isolation boundary for protected verifier artifacts. Decision: validation and release configurations require a container runtime; unit tests may use local pure functions only.
4. **Training installation:** `prime-rl` expects a source workspace with pinned submodules and NVIDIA GPU(s), rather than installation as this package's Python dependency. Decision: record the source commit now and defer checkout/provider execution to P6 after owner approval.
5. **Model wording:** the upstream 1.7B example calls `PrimeIntellect/Qwen3-1.7B` a chat-template-equipped clone rather than using an `-Instruct` suffix. It is treated as the smallest suitable instruction/chat model in the allowed size range; this naming nuance is disclosed rather than silently substituted.

## P2b machine and runtime review (2026-10-25)

Observed on this machine: Ubuntu 26.04.1 LTS in WSL2, Linux kernel
`6.18.54.1-microsoft-standard-WSL2`, x86_64. Docker Engine client/server 29.9.2,
API 1.56, linux/amd64; containerd 2.4.2 and runc 1.5.2. Docker reports 16 vCPUs,
7,977,467,904 bytes RAM, cgroup v2. These are observed resources; Windows-side
WSL configuration, swap allocation and VM configuration files were not inspected.
The locked project installs on Python 3.14.4. The unchanged suite passed before
implementation (see `results/p2b_gate.json`).

The installed `verifiers==0.3.1` wheel supplies `verifiers.v1.Task`, `Taskset`,
`Task.score`, decorators and `DockerRuntime`, but **does not supply the
`IsolatedVerifierEnv` previously claimed in this note**. The earlier compatibility claim was
incorrect for this installed artifact. P2b therefore implements an E1-specific
`DockerRuntime` subclass, a concrete v1 Taskset, and host-side protected scoring
with submitted source executed in disposable solver/replay containers. No
untrusted code executes in the host verifier process. The local scripted adapter
exercises setup, finalize, and the real `Task.score` reward hooks without a model.
Round 2 adds a standard v1 `eval` plugin path for scripted validation; model-backed and remote runtime execution remain unsupported and are refused.

The only bind mount is a unique work directory under `/home/kartik/qi-sandbox`,
mounted at `/work`. Dev oracle provenance is written under `/home/kartik/qi-private`,
which is never mounted. Existing sealed seed manifests remain untouched. Both
external directories were explicitly requested by the owner in the P2b prompt.
Containers use network `none`, a read-only root filesystem, no privileged mode,
no Docker socket, no host PID namespace, pids limit 32, 128 MiB memory and 1 CPU.
Docker's implicit system mounts still exist; “one mount” means one declared
Docker mount, not absence of `/proc` and other standard container system mounts.

A root-owned strace process supervises commands as `nobody`; only its parent has
SYS_PTRACE, SETUID and SETGID capabilities, needed for UID separation and tracing.
All other capabilities are dropped, and no-new-privileges is enabled. Submitted
code has no elevated UID. File syscall traces cross the Docker boundary; reads
of the canary and access to protected harness/private paths cause a hard zero.
Initial runtime commands also retain these flags through finalization. Live
processes and background services are explicitly unsupported. The image base is
pinned by digest and strace is pinned; runtime inspection records the actual image.

Fresh dev replay seeds are derived deterministically from primary seed, tier and
source hash. They are different from the primary seed, but predictable; they are
not claimed to be a cryptographically sealed holdout. Round-1 batched execution has been removed. Round 2 uses complete independent v1 rollouts and distinct solver, primary and replay containers for each valid case, with protected answers on the host. Invalid/flagged submissions fail closed before replay.


## P2b round 2: current official docs and Hub execution

Checked 2026-10-25 against the official
[Verifiers v1 overview](https://github.com/PrimeIntellect-ai/verifiers/blob/v0.3.1/docs/v1/overview.md),
[v1 evaluation guide](https://github.com/PrimeIntellect-ai/verifiers/blob/v0.3.1/docs/v1/evaluation.md),
and [Prime CLI Environments Hub guide](https://github.com/PrimeIntellect-ai/prime#environments-hub).
The overview describes the Hub as a collection of installable tasksets and an
agent as harness × model × runtime policy. The evaluation guide explicitly
selects a runtime under `env.agent.runtime`; installation does not establish a
particular sandbox boundary. Prime CLI documents `prime env install` as local
installation. These sources do not establish a universal “Hub's own sandbox”
that automatically reproduces this project's Docker flags or host-private paths.

A locally Hub-installed package must export the taskset and its checked Env,
have the required immutable Docker image available, and have explicitly prepared
work/private paths. The package loader resolves `qi-e1` to `E1Taskset`, `E1Env`
and `E1Harness`; the Env owns provisioning. Generic Env/runtime bypasses are
refused at task setup. The ordinary v1 CLI is **`eval`** in this installed wheel;
`vf-eval` is its legacy CLI. The local no-model validation invocation is:

```bash
uv run eval @ configs/e1_scripted.toml --no-serve --no-rich --no-push
```

The committed config selects a design seed, local dummy model endpoint and no
upload; its scripted harness never contacts that endpoint. The complete normal
Env/Agent/Task lifecycle runs. Remote Prime sandboxes, hosted Hub evaluation,
interactive model harnesses and training are **not certified** by this local
path. E1 refuses unsupported harnesses/runtimes rather than silently substituting
a generic boundary. Docker Engine access and the two named host directories are
required. No Hub publication or remote execution was attempted.

The source read API, including `_read`, now uses traced solver-UID commands.
O_NOFOLLOW, nonblocking open, regular-file checks, size-before-read and a bounded
read reject unsafe source transfers; the host checks the received length again.
The gate uses a source/design/image freeze and a one-shot call marker. Numeric
reward and task-case construction are versioned separately from the frozen P1
generator. No frozen gate threshold, weight or tolerance changed.

## P2c E5 and shared runtime extraction

P2c moves the checked Docker implementation and bounded audited transfer/execution
helpers into `src/qi_runtime/`. E1 retains a compatibility adapter and unchanged
case/reward semantics; its prior frozen experiment remains identified by its
historical commit rather than being silently relabelled after this extraction.
E1 regression evidence for the extraction is in `logs/p2c_e1_regression.xml`.
The shared image can be selected by `QI_RUNTIME_IMAGE_DIGEST`, with the old E1
variable retained as a fallback; only immutable image IDs are accepted.

E5's canonical plugin is `qi-cost-realism` (`qi_cost_realism` Python module), with
`qi-e5` retained as an internal alias. Its checked Env uses the same runtime class
as E1. Submitted source produces a gross weight path and claims; the host
recomputes all costs, capacity enforcement, net Sharpe and holding days itself.
No numeric-only or cost-awareness self-attestation can establish correctness.
The scripted-only/remote-model limitations above remain. Detailed third-party
execution, oracle placement and public-claim limits are in
[reports/hub_architecture.md](reports/hub_architecture.md).

The E5 local CLI validation config is `configs/e5_scripted.toml`, run with `eval`
and uploads disabled. It uses design seeds only. Remote GitHub CI status must be
read from actual Actions records and reported separately from local test success;
missing API access is not reported as a pass.


## P2d E6 task-layer reconciliation

E6 exports canonical `qi-data-traps` through `qi_data_traps`, using the same
checked qi_runtime and immutable image as E1/E5. The generator source is frozen;
E6 selects event windows from a 1000-asset, 500-session synthetic configuration
inside its registered ranges. Only the quote feed is corrupted in the task
layer; host oracle truth records original/altered records. Independent audited
returns, registry and action notices make repairs identifiable. Clean corporate
actions and large moves are decoys, not anomalies. The old direct active-ID
set score is retired. The local scripted v1 path, predictable replay, trusted
host oracle boundary and unsupported hosted/model harness caveats in
reports/hub_architecture.md apply equally to E6. No Hub publication occurs.
