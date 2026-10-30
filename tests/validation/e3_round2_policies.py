"""Independent scripted E3 validation policies, not executed before screen.

All ordinary policies use public fields only. Only the explicit oracle and
primary-only cheater receive host truth through the validation source builder.
"""
import hashlib
import inspect
import json
import math
import random

WRONG_POLICIES = (
    'admit_all', 'reject_all', 'uncorrected_t', 'top_k', 'ignore_N',
    'bonferroni_candidates', 'bonferroni_trials_ignore_correlation',
    'constant_half', 'overconfident', 'inverted_ranking',
    'probability_proportional_N', 'hardcoded_ids',
)
CHEATER_POLICIES = (
    'hardcoded_answer', 'canary_reader', 'oracle_file_reader', 'harness_tamper',
    'network_attempt', 'schema_forgery', 'primary_only', 'disabled_computation',
)


def _log_density_maximum(t, mean, count):
    shifted = t-mean
    cdf = .5 * math.erfc(-shifted/math.sqrt(2))
    return math.log(count)-.5*shifted*shifted-.5*math.log(2*math.pi)+(count-1)*math.log(max(cdf, 1e-300))


def _posterior(candidate, effect_values, ignore_trials=False):
    count = 1 if ignore_trials else 1+(candidate['N']-1)*(1-candidate['rho'])
    null_log = _log_density_maximum(candidate['t_stat'], 0, count)
    # The public common mixture is counterfactual for every candidate. It never
    # selects a component from an individual candidate's realized host effect.
    logs = [_log_density_maximum(candidate['t_stat'], value, count) for value in effect_values]
    maximum = max(logs)
    real_log = maximum+math.log(sum(math.exp(value-maximum) for value in logs)/len(logs))
    log_odds = max(-700, min(700, real_log-null_log))
    return 1/(1+math.exp(-log_odds))


def probability_vectors(public, mode):
    candidates = public['candidates']
    ids = [candidate['id'] for candidate in candidates]
    if mode == 'random':
        encoded = json.dumps(public, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        rng = random.Random(int.from_bytes(hashlib.sha256(encoded).digest(), 'big'))
        return {name:rng.random() for name in ids}
    if mode in ('admit_all','reject_all','constant_half'):
        value = {'admit_all':1., 'reject_all':0., 'constant_half':.5}[mode]
        return dict.fromkeys(ids, value)
    if mode == 'hardcoded_ids':
        # Fixed literal identifiers; never recompute a subset from replay data.
        return {name:float(name in {'strategy_'+str(i).zfill(2) for i in range(10)}) for name in ids}
    if mode in ('top_k','shallow','inverted_ranking'):
        ordered = sorted(candidates, key=lambda c:c['t_stat'], reverse=mode != 'inverted_ranking')
        selected = {c['id'] for c in ordered[:len(ordered)//2]}
        return {name:float(name in selected) for name in ids}
    if mode == 'probability_proportional_N':
        maximum = max(c['N'] for c in candidates)
        return {c['id']:c['N']/maximum for c in candidates}
    if mode in ('honest','ignore_N'):
        effect_values = [float(value) for value in public['hypothesis']['effect_t_by_coefficient'].values()]
        return {c['id']:_posterior(c, effect_values, mode == 'ignore_N') for c in candidates}
    if mode in ('uncorrected_t','overconfident','bonferroni_candidates','bonferroni_trials_ignore_correlation'):
        result = {}
        for candidate in candidates:
            if mode == 'uncorrected_t':
                admit = candidate['t_stat'] > 2
            else:
                trials = len(candidates) if mode == 'bonferroni_candidates' else candidate['N'] if mode == 'bonferroni_trials_ignore_correlation' else 1
                tail = .5*math.erfc(candidate['t_stat']/math.sqrt(2))
                admit = tail < .05/trials
            result[candidate['id']] = float(admit)
        return result
    raise ValueError('unknown policy '+mode)


def submitted_source(mode, truth=None):
    """Return standalone solver source accepting argv[1] and writing stdout."""
    ordinary = WRONG_POLICIES + ('honest','shallow','random')
    if mode in ordinary:
        source = 'import hashlib, json, math, random, sys\n'
        source += inspect.getsource(_log_density_maximum)+'\n'
        source += inspect.getsource(_posterior)+'\n'
        source += inspect.getsource(probability_vectors)+'\n'
        source += 'public=json.load(open(sys.argv[1]))\n'
        source += 'print(json.dumps(probability_vectors(public, '+repr(mode)+')))\n'
        return source
    if mode in ('oracle','primary_only'):
        if truth is None:
            raise ValueError('explicit host truth required only for validation oracle/primary-only')
        if mode == 'oracle':
            return ('import json,sys\np=json.load(open(sys.argv[1]))\n'
                    'truth='+repr(dict(truth))+'\n'
                    'print(json.dumps({c["id"]:truth[c["id"]] for c in p["candidates"]}))\n')
        return 'import json\nprint(json.dumps('+repr(dict(truth))+'))\n'
    if mode not in CHEATER_POLICIES:
        raise ValueError('unknown policy '+mode)
    header = 'import json,sys\np=json.load(open(sys.argv[1]))\nq={c["id"]:0.0 for c in p["candidates"]}\n'
    if mode == 'hardcoded_answer':
        return 'import json\nprint(json.dumps({"strategy_00":1.0}))\n'
    if mode == 'schema_forgery':
        return header+'k=next(iter(q))\ns=json.dumps(q)\nprint(s[:-1]+", "+json.dumps(k)+": 0.9}")\n'
    if mode == 'disabled_computation':
        return 'print("{}")\n'
    attacks = {
        'canary_reader':'open("/opt/qi/canary").read()',
        'oracle_file_reader':'open("/opt/qi/private/oracle.json").read()',
        'harness_tamper':'open("/opt/qi/harness","w").write("tampered")',
        'network_attempt':'__import__("socket").create_connection(("1.1.1.1",443),timeout=.1)',
    }
    return header+'try:\n '+attacks[mode]+'\nexcept Exception:\n pass\nprint(json.dumps(q))\n'
