# P5a model harness: prospective design

P5a builds infrastructure using synthetic dev cases and mock responses. Provider calls are locked, real key values must not be inspected, and the paid pilot cannot run in this task. The only HTTP test is an explicitly enabled loopback fake server using a deliberately planted fake credential. Empty committed prices cannot authorize any call. No baseline, training, sealed evaluation, or E3 experiment is performed.

The implementation reuses the unchanged checked runtime and unchanged E1, E2, E5 and E6 task setup/finalize/reward implementations. A separate v1 Env adapter selects the model harness instead of weakening the existing scripted-only Env checks. The E3 prototype on main is unvalidated and is skipped; the separate e3-redesign branch is not silently merged or activated.

## Multi-step boundary

One inspected solver container persists for an episode; commands execute as separate bounded solver-UID processes. Files persist, Python process state does not. Network remains none, root filesystem read-only, one declared work bind, fixed immutable image, fixed pids/memory/CPU limits, traced solver commands, canary/harness protections, and host-only grading. The host client and its credentials never run inside or enter the container.

Existing trusted runtime.write is used only by unchanged task setup, before model actions. Model-influenced writes must use audited solver-UID helpers with componentwise dirfd and O_NOFOLLOW confinement. File tools reject traversal, nonregular files, links, and paths outside /work. The adapter adds conservative write-path trace auditing for implicit writable container locations such as /dev/shm. Uncertain, truncated or unsupported audit evidence ends the episode rather than permitting continued execution. Host timeout, transport failure or cancellation destroys the container before any continuation. Source finalization and primary/fresh replay remain unchanged.

Each model command first clears its inherited environment, then supplies only the fixed public PATH=/usr/local/bin:/usr/bin:/bin, LANG=C.UTF-8 and PYTHONDONTWRITEBYTECODE=1. This preserves existing programs that launch Python subprocesses while preventing inherited host values. Host credentials are never mounted, passed as solver arguments, or included in container environment. This prevents host-environment exposure; it does not claim to detect every in-process getenv query. Containers necessarily contain readable system libraries; work-file tools are confined, while ordinary interpreter/library reads remain necessary for command execution. No remote or generic runtime is certified.

## Limits and termination

Defaults committed before validation: 16 model turns, 2048 completion tokens per turn, 32768 total tokens, 180 seconds per episode, 16384 bytes per visible tool output, and 2097152 transcript bytes. Counts and byte bounds are positive integers; timeout is positive and finite. The runtime's existing 20-second command timeout and resource constraints remain in force. No submission, an exceeded limit, an uncertain command outcome, or a security violation produces a defined zero with a recorded termination reason. Cleanup is unconditional.

## Spend and pilot authorization

Prices are a committed empty template; owner-supplied prices are required later. Actual costs use returned token usage and Decimal prices, with the caps and 80-percent stopping rule from prereg.yaml via scripts/budget_gate.py. Locked outstanding reservations cover conservative call bounds and are not recorded as paid spend. Lost responses retain unresolved reservations and stop further dispatch. Actual usage exceeding a reservation is recorded in full and stops; it is never concealed as a refused cost. Such a provider-bound violation is a limitation requiring owner reconciliation, not a proof that arbitrary provider billing can never exceed its declared limits.

The pilot entrypoint remains locked in P5a even when --confirm-spend is supplied. It must reject before reading a credential or opening a connection. No spend-cap override exists. A later owner-authorized phase must review/unlock the provider path, fill prices, and reconcile any outstanding reservation. Filling a key variable alone cannot enable calls. Planned default is two episodes per environment/tier cell (32 per model across four environments), satisfying the preregistered 20-episode pilot floor; default seed windows must be checked against all historical gate populations before use.

Baseline projections use observed token totals divided by observed episode counts and owner prices. They preserve frozen episode counts and at least two API plus two open models. Extra baseline models are removed before reducing training seeds. Training GPU projection requires a separate measured per-seed amount; it is never invented from baseline API tokens. Reducing training seeds cannot fix excessive baseline API cost. Projections report unavailable components explicitly and respect the 80-percent stop bound as well as hard caps.

## Prompts, transcripts and equivalence

Per-environment prompts and tool descriptions are content-hashed in an append-only prompt manifest. Later changes require a new dev-only manifest entry; old entries must remain, and sealed outcomes must never select prompts. No prompt is tuned on model results in P5a.

Transcripts contain bounded, hashed messages, tool calls, visible outputs, token counts, time, reward, termination reason and hack monitors. Known credentials are redacted before recording. Full credentials, HTTP authorization headers, raw provider errors and host environment dumps are never recorded. Hashes make truncation and storage scope explicit; a bounded transcript must not silently drop a whole episode.

Actual mock-oracle, wrong-policy and cheater trajectories are compared with the existing scripted harness on identical dev inputs. Semantic primary/replay records include answers, numerical results, status, flags and submitted source identity. Separate fresh rollouts necessarily have different container IDs, command trace hashes and timing: those operational fields are excluded from equivalence, with original provenance retained separately. Numeric comparisons use 1e-12. This is mock tool-path equivalence, not evidence that a real model follows instructions or succeeds at research.

A later pilot measures reward density, turns, tokens, cost and hack monitors on dev seeds. It will not estimate sealed-test performance, training transfer, broad research integrity, or real-market usefulness. Infrastructure validation results and any unsupported boundary will be recorded in reports/P5a.md before STOP.
