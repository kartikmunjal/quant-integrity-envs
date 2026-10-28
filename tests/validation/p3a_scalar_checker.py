"""Independent P3a scalar path, written from design before implementation.

No production imports. Execution/error extraction is intentionally upstream: this
checker consumes immutable observed records and does not execute patch source.
"""
import math


def matching(findings, truth):
    """Maximum bipartite cardinality, independently handles overlapping spans."""
    assigned = {}
    def augment(i, visited):
        f = findings[i]
        for j, t in enumerate(truth):
            if j in visited or f['family'] != t['family']:
                continue
            if not t['line'] <= f['line'] <= t.get('end_line', t['line']):
                continue
            visited.add(j)
            if j not in assigned or augment(assigned[j], visited):
                assigned[j] = i
                return True
        return False
    for i in range(len(findings)):
        augment(i, set())
    tp = len(assigned)
    return tp, len(findings)-tp, len(truth)-tp


def quality(error):
    if not math.isfinite(error) or error >= .01:
        return 0.
    if error <= .0001:
        return 1.
    x = (error-.0001)/.0099
    return 1.-3.*x*x+2.*x*x*x


def check_record(record, exponent=1):
    if not record.get('schema_ok', True) or not record.get('security_ok', True):
        return 0.
    tp, fp, fn = matching(record['findings'], record['truth'])
    if record['truth']:
        detection = (2.*tp/(2*tp+fp+fn))**exponent
        clean = 1.
    else:
        detection = 1.
        clean = (1.+fp)**(-exponent)
    grades = []
    for key in ('primary_error', 'replay_error'):
        patch = quality(max(record[key], record.get('poison_error', 0.)))
        if min(detection, patch, clean) <= 0.:
            grades.append(0.)
        else:
            grades.append(1./(.4/detection+.4/patch+.2/clean))
    return min(grades)
