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
