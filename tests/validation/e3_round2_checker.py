"""Independent E3 round-two checker; imports no production scoring helpers."""
from fractions import Fraction


def candidate_loss(probability, outcome):
    """Integrate the weight polynomial independently of closed-form production."""
    p = Fraction(probability)
    weight = {3: Fraction(1), 4: Fraction(-1)}
    terms = {}
    for exponent, coefficient in weight.items():
        terms[exponent + 1] = terms.get(exponent + 1, 0) + coefficient * (1 if outcome == 0 else -1)
        if outcome == 1:
            terms[exponent] = terms.get(exponent, 0) + coefficient
    lower, upper = (Fraction(0), p) if outcome == 0 else (p, Fraction(1))
    return sum(coefficient * (upper ** (degree + 1) - lower ** (degree + 1)) / (degree + 1)
               for degree, coefficient in terms.items())


def execution(probabilities, truth):
    if len(probabilities) != len(truth) or not truth:
        raise ValueError('nonempty matched vectors required')
    total = sum(candidate_loss(q, y) for q, y in zip(probabilities, truth, strict=True))
    mean_loss = total / len(truth)
    normalized = 1 - mean_loss / Fraction(3, 400)
    return max(Fraction(0), min(Fraction(1), normalized))


def paired(primary, replay, *, valid_schema=True, safe_execution=True, tamper=False):
    if not valid_schema or not safe_execution or tamper:
        return 0.0
    return min(primary, replay)


def audit_record(record):
    """Recompute a stored rollout reward from raw answers, never stored rewards.

    Missing evidence and any schema/security/execution failure fail closed.
    Truth remains host-side input to this independent post-execution checker.
    """
    import math
    if record.get('schema_ok') is not True or record.get('security_ok') is not True:
        return 0.0
    solver = record.get('solver')
    if not isinstance(solver, dict) or solver.get('flagged', True) is not False:
        return 0.0
    computed = []
    for name, truth_key in (('primary','truth'), ('replay','replay_truth')):
        stage = record.get(name)
        truth = record.get(truth_key)
        if not isinstance(stage, dict) or not isinstance(truth, dict) or not truth:
            return 0.0
        if stage.get('flagged', True) is not False or stage.get('exit_code') != 0:
            return 0.0
        answer = stage.get('answer')
        if not isinstance(answer, dict) or set(answer) != set(truth):
            return 0.0
        for name in truth:
            probability, outcome = answer[name], truth[name]
            if (type(probability) not in (int,float) or not math.isfinite(probability)
                    or not 0 <= probability <= 1 or type(outcome) not in (int,bool)
                    or outcome not in (0,1)):
                return 0.0
        computed.append(execution([answer[key] for key in truth],list(truth.values())))
    return float(min(computed))


def uniform_expectation_upper_bound():
    """Deterministic quadrature bound for K20/r10 independent uniform reports.

    Each q-cell is assigned its minimum loss, then rounded DOWN to a lattice.
    Hence this discrete expected clipped reward bounds the continuous value
    above, apart from FFT floating-point error (guarded conservatively in tests).
    This is a mathematical distribution calculation, never an episode run.
    """
    import numpy as np
    cells = 4000
    spacing = 1e-5
    endpoints = np.arange(cells + 1, dtype=float) / cells
    # Null loss increases and real loss decreases on [0,1].
    null_q, real_q = endpoints[:-1], endpoints[1:]
    null_losses = null_q ** 5 / 5 - null_q ** 6 / 6
    real_losses = 1 / 60 - real_q ** 4 / 4 + 2 * real_q ** 5 / 5 - real_q ** 6 / 6
    null_bins = np.floor(np.maximum(null_losses, 0) / spacing).astype(int)
    real_bins = np.floor(np.maximum(real_losses, 0) / spacing).astype(int)
    transform_size = 1 << 17  # exceeds maximum sum-support; no cyclic aliasing.
    null_mass = np.bincount(null_bins, minlength=transform_size) / cells
    real_mass = np.bincount(real_bins, minlength=transform_size) / cells
    joint = np.fft.irfft(np.fft.rfft(null_mass) ** 10 * np.fft.rfft(real_mass) ** 10,
                        n=transform_size)
    assert abs(float(joint.sum()) - 1) < 1e-10
    assert float(joint.min()) > -1e-12
    reward = np.maximum(1 - np.arange(transform_size) * spacing / (20 * .0075), 0)
    return float(joint @ reward)
