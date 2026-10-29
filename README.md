# Quant Research Integrity Environments

Synthetic environments for testing quantitative research integrity with
deterministic verifiers. The research design and frozen values are recorded in
[SPEC.md](SPEC.md) and [prereg.yaml](prereg.yaml).

## In progress

The mutation engine and E2 (`qi-leakage-audit`) are implemented. Their first
fresh gate **failed and remains incomplete** following an infrastructure
classification issue: a denied harness-tampering attempt was followed by a
Docker host timeout during submission transfer. The frozen classification rule
treated the collision as terminal policy evidence, so no retry occurred. The
underlying host-stall cause is unknown. A fix and a new gate are planned;
neither is reported as completed.

These are **partial gate observations, not a gate pass**:

| Observation | Recorded result |
|---|---|
| Planned rollouts | 8,200 |
| Completed rollouts | 5,657 |
| Terminal failures | 1 |
| Unexecuted rollouts | 2,542 |
| Retries | 0 |
| Scripted oracle mean reward | 1.0 in each tier; 500 completed per tier |
| Random policy mean reward | 0.0 in each tier; 50 completed per tier |
| Largest conceptual wrong-policy mean | 0.02; all twelve policies completed 50 cases per tier |
| Clean oracle false-positive rate | 0 / 500 |
| Independent scalar-checker agreement | 1.0 on the 5,657 completed records |

Later fresh controls, including the shallow detector, were not reached. Passing
observed cells does not establish completion or overall validation. M1 has not
been reached.

Source: [partial gate result](results/p3a-gate.json),
[completion audit](results/p3a_gate_audit.json),
[phase report](reports/P3a.md), and
[independent post-gate review](reports/P3a_gate_review.md).
These E2 observations use generator version
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`
and implementation `d0eecc88b005d14ddec3a6a2f09a22881fb35e8c`.
The failed gate and its consumed marker are retained as historical evidence.

## Limitations

- E2 uses **one synthetic script template with twelve mutations, each in three
  realizations**. Its scripted oracle demonstrates solvability within that
  template grammar, **not model performance** or general code-auditing ability.
- All data are synthetic; real-market validity is not established.
- Validation uses the project's checked local Docker execution. Hosted Hub and
  model-harness compatibility are not established.
- The independent scalar checker consumes recorded execution errors; its
  agreement is not an independently implemented financial numerical oracle.

See [milestones](docs/MILESTONES.md) for completion requirements and claim
boundaries. The owner will run release review; no release-review pass or public
release is claimed here.
