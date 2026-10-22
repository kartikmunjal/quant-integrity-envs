# AGENTS.md: standing rules for every session in this repo

You are a coding agent building `quant-integrity-envs`. Read these files at the start of every session, in this order: AGENTS.md, SPEC.md, prereg.yaml, AMENDMENTS.md, COMPAT.md (once it exists). Then do exactly the phase prompt you were given and nothing else.

## 1. Independence
- Work only inside this repository directory. Do not list, read, copy from, or import any other project, repo, notebook, or data folder on this machine. Scratch space and package caches are fine.
- Use synthetic data only. Do not download or use real market data, licensed data, or anyone's research data.
- Never reuse credentials, keys, or config from anywhere else. Keys you are given for this project come from environment variables and are never written to a file, log, or commit.
- If a task seems to need something outside the repo, STOP and report instead of working around it.

## 2. Network
Allowed: package registries; the official documentation and source repositories for the verifiers library and the Environments Hub; the model-provider APIs named in the phase prompt, only through the budget-gated runner; the GPU provider the owner names for Phase 6. Nothing else.

## 3. Pre-registration and amendments
- `prereg.yaml` is frozen at the end of Phase 0 (`frozen: true`, git tag `prereg-v1`). After that, it changes only through a dated entry in `AMENDMENTS.md`.
- An amendment states: what changed, why, the date, the commit hash, and an attestation that no sealed-test result or baseline result had been seen when it was made.
- Never rewrite or squash history. Never edit a frozen value silently. Never change a threshold, tier, grid, or held-out family after seeing any result.

## 4. Test isolation
- Sealed-test seeds are used only by `scripts/run_sealed_eval.py`. It must refuse to run unless the marker file `FROZEN_EVAL` exists, and it logs every call to `logs/sealed_eval_calls.csv`.
- `FROZEN_EVAL` is created once, in the Phase 5 gate, after the evaluation set hash is committed.
- No sealed-test metric of any kind is computed during development. Use dev seeds for everything else, including prompt and hyperparameter choices.

## 5. Honesty
- Report what happened. A failed gate, a null result, or a surprising reward hack is a finding, not an embarrassment.
- Never fabricate numbers, citations, human labels, or agreement statistics. Trajectory reviews are labelled "author-reviewed".
- Every reported number must be reproducible from a file in `logs/` or `results/` and must name the environment and generator version hash it came from.
- Never weaken a verifier, loosen a threshold, or drop an episode to make a gate pass.

## 6. Dual control
The author of a verifier does not validate it. For each verifier, write the validation tests in `tests/validation/` first, then implement. If you can start an independent reviewer session, do so for each verifier and record that in the phase report. If you cannot, say so plainly in the report.

## 7. Money
- Never spend on model APIs or GPUs outside the budget gate. Every call that costs money goes through `scripts/budget_gate.py`, which reads the caps in `prereg.yaml`, appends to `logs/spend.csv`, and refuses at 100 percent of a cap.
- At 80 percent of any cap, STOP and report.
- Pilots measure real cost before any full run. Full runs are sized from pilot numbers, never from guesses.

## 8. Engineering standards
- Deterministic seeding everywhere. The same seed and version hash must give identical bytes.
- Pinned dependencies, a lockfile, and CI that runs the full test suite.
- Every module has tests. Every environment has: a schema file, an oracle, a verifier, scripted policies, and validation tests.
- Small commits with clear messages. Do not push to any remote unless the phase prompt says to.
- Never commit data caches, keys, model weights, or large logs.

## 9. Release review
`scripts/release_review.py` scans the committed files and the full git history for terms listed in the file whose path is in the environment variable `RELEASE_REVIEW_TERMS`. That file lives outside this repo and belongs to the owner. You may run the script. You must not open that terms file, print its contents, copy it, or try to infer what is in it. The script prints only pass or fail and the file and line of any hit.

## 10. Stop-and-report
Every phase ends with a STOP and a report that contains:
1. What was built, with commit hashes.
2. Each gate criterion, its measured value, and pass or fail.
3. Anything underspecified that you had to interpret, with the interpretation you chose.
4. Anything that surprised you.
5. Spend and compute used, from the logs.
Do not begin the next phase. Wait for the owner.

## 11. Never do
- Read or modify the oracle, the sealed manifests, or the evaluation harness from inside an agent-facing sandbox.
- Run any model on sealed-test seeds before the `FROZEN_EVAL` marker exists.
- Train on a sealed-test seed or on a held-out family for its own fold.
- Publish anything (package, Hub, repo, post) without explicit owner approval in the prompt.
