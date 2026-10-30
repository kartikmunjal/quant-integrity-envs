"""Independent exact polynomial-integration checker; no E3 code imports."""
from fractions import Fraction


def loss(probability, outcome):
    # Construct integrands from w(t)=t^3(1-t), rather than the closed forms.
    weight = [0, 0, 0, 1, -1]
    integrand = [Fraction(0)] * 6
    for power, coefficient in enumerate(weight):
        integrand[power + 1] += coefficient if outcome == 0 else -coefficient
        if outcome == 1:
            integrand[power] += coefficient
    def integral_at(endpoint):
        return sum(coefficient * endpoint ** (power + 1) / (power + 1)
                   for power, coefficient in enumerate(integrand))
    if outcome == 0:
        return integral_at(probability)
    return integral_at(Fraction(1)) - integral_at(probability)


def reward(report, truth):
    baseline = sum(loss(Fraction(0), y) for y in truth)
    if baseline == 0:
        return None
    submitted = sum(loss(q, y) for q, y in zip(report, truth, strict=True))
    ratio = (baseline - submitted) / baseline
    return max(Fraction(0), min(Fraction(1), ratio))
