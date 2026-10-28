# Project milestones

## M1: application-ready

M1 is reached after P3a passes and the application-ready package below is complete:

- Validated synthetic generator, E1, E2, E5, E6 and mutation engine.
- A paper-style README with the data card, design notes, per-environment and
  per-tier validation tables, Hub-architecture limitations and reward sensitivity
  tables.
- `scripts/release_review.py` reports PASS on the full git history. The owner's
  private terms file is used only by that script and is never opened by an agent.
- Repository renaming and public visibility occur only on explicit owner approval.
- Resume bullets are generated only from numbers recorded in `results/`.

Allowed M1 claims concern design, validation and anti-hacking controls, supported
by gate numbers, and stated plans for baselines and training.

M1 does not support claims about model performance, training results, Hub or
hosted-runtime compatibility, or real-market validity. All data are synthetic.

## Optional M1.5

A clearly labelled dev-seed model pilot may follow owner authorization and the
budget gate. It is not the pre-registered evaluation and must not be presented as
one.

## Owner decision after P3a

After P3a, STOP and wait for the owner to choose whether to package M1 or continue
to E3. E3 may be added before M1 only if the owner says so. Passing P3a alone does
not authorize packaging, a repository rename, public visibility, model runs,
training, Hub publication, P4 or P5.
