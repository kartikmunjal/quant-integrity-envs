# Independent E1 agent review, P2b

Reviewer session `/root/e1_review`, separate from implementation. Initial review
executed the dev core exploit: valid zero numeric answers with availability=True
earned 0.2. Later runtime reviews were read-only. No independent human labels.

Findings addressed before bulk gate: self-attested availability replaced by fresh
source re-execution; initial runtime `run()` calls traced and flags retained;
live/background processes reject; source writes constrained to /work; overflow
schema errors caught; workspace symlinks checked before resolving; taskset counts
constrained. A full setup/finalize/reward regression demonstrates initial-session
canary evidence persists after clean source submission.

Remaining findings, left explicit at STOP:

- Inherited `_read()` directly invokes Docker cat without tracing. Direct reads
  through this API are not covered by the `run()` audit claim.
- Finalization checks source size after transfer; the inherited read is not bounded
  before transfer.
- Bulk policy gates batch public inputs in a shared interpreter and attach trusted
  host results before Task.score. They do not exercise the complete independent
  per-episode setup/finalize lifecycle for each measured case.
- Agreement checks independently recompute numeric truths and valid unflagged
  answer patterns, but omit malformed, flagged and divergent replay cases.
- The local image tag is mutable; image identity must accompany gate provenance.
- No standard Env/CLI factory selecting the custom runtime was certified.
- Typical wrong-return algorithms receive 0.4, above the frozen 0.10 ceiling.
  The gate includes these failures rather than suppressing them.

The reviewer also noted that original tiers differ only in cutoff. P2b's as-of
oracle now handles revisions explicitly, but this does not establish distinct
pedagogical difficulty tiers or repair insufficient availability-date stress.
