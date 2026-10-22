# Separation review checklist

Owner review is required before the preregistration freeze. The coding agent must not sign this checklist.

## Repository and data independence (AGENTS.md section 1)

- [ ] This repository is standalone and contains no imported code, notebooks, datasets, or configuration from another local project.
- [ ] Only synthetic data will be generated or used.
- [ ] No real, licensed, private, or research market data is present.
- [ ] Credentials and keys are supplied only through project-specific environment variables and are never written to tracked files or logs.
- [ ] Oracle outputs and sealed manifests will live outside every agent-facing sandbox mount.

## Network boundaries (AGENTS.md section 2)

- [ ] Development network access is limited to package registries and official Verifiers/Environments Hub documentation and source.
- [ ] Model-provider traffic will occur only for models named in the applicable phase and only through `scripts/budget_gate.py`.
- [ ] GPU-provider access will not occur before P6 and will use only the provider named by the owner.
- [ ] Agent-facing sandboxes have network access disabled.

## Release review boundary (AGENTS.md section 9)

- [ ] `RELEASE_REVIEW_TERMS` points to a private owner-controlled file outside this repository.
- [ ] Agents and project scripts do not print, copy, commit, or attempt to infer the terms.
- [ ] `scripts/release_review.py` reports only PASS/FAIL and hit locations.
- [ ] Release review scans both the current working tree and full Git history.
- [ ] Publication remains blocked until P7 review passes and the owner explicitly approves publication.

## Owner sign-off

Owner name: ______________________________

Signature: _________________________________

Date (YYYY-MM-DD): ________________________

Decision: [ ] approved for preregistration freeze  [ ] changes required
