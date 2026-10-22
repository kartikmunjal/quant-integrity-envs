# Compatibility note

Checked against official upstream documentation and source on 2026-10-21. These pins are the P0 integration target; changes require an explicit compatibility review.

## Pins

- Python: `>=3.11,<3.15` (CI uses 3.11).
- `verifiers==0.3.1`, tag commit `b2e4e8157783b2c0dffc7821044c87f29f1c3ccf`.
- `prime-rl` commit `477d438193e77df3a45edab58e478fad3cde32df` for the Phase 6 training workspace. It is pinned by commit because the official training path is a source checkout with submodules, not a dependency of this environment package.
- Phase 6 base model: `PrimeIntellect/Qwen3-1.7B`. This is the smallest model in the preregistered 1.5B–3B interval shown in an official prime-rl multi-turn RL example. The upstream Wordle guide describes it as a clone of `Qwen/Qwen3-1.7B` with a chat template suitable for multi-turn RL.

Project dependencies are pinned in `pyproject.toml`; the CI installation set is pinned in `requirements.lock`.

## Verifiers v1 structure

In v1, the Hub unit is a **taskset**, not a monolithic legacy environment. A `Taskset[TaskT, ConfigT]` loads serializable `TaskData` rows and task behavior. A task supplies lifecycle hooks, tools, metrics, and deterministic rewards using decorators such as `@vf.metric` and `@vf.reward`. An `Env` controls one or more agents and produces an `Episode`; for this project, the expected control flow is normally `SingleAgentEnv` or `IsolatedVerifierEnv`.

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

`IsolatedVerifierEnv` destroys the solver runtime, transfers only declared artifacts, and restores them into a fresh verifier runtime before scoring. The verifier must use Docker, Prime, or another container runtime; host subprocess mode intentionally refuses absolute artifact restoration. Network policy is reapplied before scoring. These boundaries fit the SPEC requirement that the agent cannot access the oracle, sealed manifests, or server-side ledger.

The current v1 API describes decorated deterministic rewards and metrics rather than the legacy rubric abstraction. Project reward weights from `prereg.yaml` will be composed as deterministic `@vf.reward` outputs. Hard gates are checked before weighted terms. No model-backed judge is configured.

Canary reads and harness mutation are runtime evidence recorded outside agent-writable artifacts. Oracle material and sealed manifests are staged only in the isolated verifier runtime. Phase implementations must verify these assumptions against the pinned runtime with integration tests.

## Publishing and local evaluation

The official CLI flow is:

- scaffold/validate locally with `vf-init`, `vf-validate`, and `vf-eval`;
- keep evaluation local with `vf-eval ... --no-push` during development;
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
2. **Environment packaging:** SPEC speaks of six environments; the current Hub exposes user-created tasksets paired with an `Env` control-flow implementation. Decision: ship six taskset packages and select `IsolatedVerifierEnv` for protected scoring.
3. **Sandbox sufficiency:** a plain subprocess runtime is not a sufficient isolation boundary for protected verifier artifacts. Decision: validation and release configurations require a container runtime; unit tests may use local pure functions only.
4. **Training installation:** `prime-rl` expects a source workspace with pinned submodules and NVIDIA GPU(s), rather than installation as this package's Python dependency. Decision: record the source commit now and defer checkout/provider execution to P6 after owner approval.
5. **Model wording:** the upstream 1.7B example calls `PrimeIntellect/Qwen3-1.7B` a chat-template-equipped clone rather than using an `-Instruct` suffix. It is treated as the smallest suitable instruction/chat model in the allowed size range; this naming nuance is disclosed rather than silently substituted.
