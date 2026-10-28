"""Single-entry weighted harmonic E2 quality and independent replay minimum."""
import math
from qi.mutate.reference import relative_error as numeric_error


def match_findings(findings,truth):
    edges=[[j for j,t in enumerate(truth) if f['family']==t['family'] and t['line']<=f['line']<=t.get('end_line',t['line'])] for f in findings]
    owners={}
    def visit(i,seen):
        for j in edges[i]:
            if j in seen: continue
            seen.add(j)
            if j not in owners or visit(owners[j],seen):
                owners[j]=i;return True
        return False
    for i in range(len(findings)):visit(i,set())
    tp=len(owners)
    return tp,len(findings)-tp,len(truth)-tp


def detection_quality(findings,truth,exponent=1):
    if not truth:return 1.
    tp,fp,fn=match_findings(findings,truth)
    return (2*tp/(2*tp+fp+fn))**exponent


def clean_quality(findings,truth,exponent=1):
    return 1. if truth else (1+len(findings))**(-exponent)


def patch_quality(error):
    if not math.isfinite(error) or error>=.01:return 0.
    if error<=.0001:return 1.
    x=(error-.0001)/.0099
    return 1-x*x*(3-2*x)


def score_components(detection,patch,clean):
    if any(not math.isfinite(x) or x<=0 or x>1 for x in (detection,patch,clean)):return 0.
    return 1/(.4/detection+.4/patch+.2/clean)


def grade_record(record,exponent=1):
    if not record.get('schema_ok',True) or not record.get('security_ok',True):return 0.
    d=detection_quality(record['findings'],record['truth'],exponent)
    c=clean_quality(record['findings'],record['truth'],exponent)
    return min(score_components(d,patch_quality(max(record[k],record.get('poison_error',0.))),c) for k in ('primary_error','replay_error'))
