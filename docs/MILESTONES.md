# Project milestones

## Current status: M1 not reached

The mutation engine and E2 are implemented, but their first fresh P3a gate
failed following an infrastructure classification issue. Of 8,200 planned
rollouts, 5,657 completed, one terminated and 2,542 were not executed; no retry
occurred. These are partial results, not a pass. A fix and a new gate are
planned; the failed gate, its source freeze and its consumed marker remain
historical evidence.

The [README](../README.md) summarizes the observed results and limitations.
Authoritative evidence is in [the partial gate result](../results/p3a-gate.json)
and [the phase report](../reports/P3a.md). These E2 results use generator version
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.
This documentation update does not implement the planned fix or authorize a
gate rerun.

## M1: application-ready

M1 is reached after P3a passes and the application-ready package below is complete:

- Validated synthetic generator, E1, E2, E5, E6 and mutation engine.
- A paper-style README with the data card, design notes, per-environment and
  per-tier validation tables, Hub-architecture limitations and reward sensitivity
  tables.
- The owner runs `scripts/release_review.py` and obtains PASS on the full git
  history. Release review is deferred to the owner for this update; no pass is
  claimed. The private terms file is never opened by an agent.
- Repository renaming and public visibility occur only on explicit owner approval.
- Resume bullets are generated only from numbers recorded in `results/`.

Allowed M1 claims concern design, validation and anti-hacking controls, supported
by gate numbers, and stated plans for baselines and training.

M1 does not support claims about model performance, training results, Hub or
hosted-runtime compatibility, or real-market validity. All data are synthetic.
E2 currently uses one synthetic script template with twelve mutations in three
realizations each. Its scripted oracle shows solvability within that template
grammar, not model performance.

## Optional M1.5

A clearly labelled dev-seed model pilot may follow owner authorization and the
budget gate. It is not the pre-registered evaluation and must not be presented as
one.

## Owner decision after P3a

After P3a, STOP and wait for the owner to choose whether to package M1 or continue
to E3. E3 may be added before M1 only if the owner says so. Passing P3a alone does
not authorize packaging, a repository rename, public visibility, model runs,
training, Hub publication, P4 or P5.
