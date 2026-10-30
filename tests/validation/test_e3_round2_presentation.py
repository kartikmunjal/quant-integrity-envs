"""Identity-only presentation contracts authored before wrapper implementation."""
import copy
import hashlib
import json


def raw_fixture(seed=1000000, prefix='old-'):
    candidates=[{'id':prefix+str(i),'N':1+i,'rho':.3,'group':i%2,
                 'returns':[.001*i,-.002,.003],'t_stat':i/10} for i in range(20)]
    ids=[c['id'] for c in candidates]
    return {'public':{'candidates':candidates,'hypothesis':{'effect_t_by_coefficient':{'0.5':1.2}}},
            'truth':{name:i%2 for i,name in enumerate(ids)},
            'effects':{name:.001*(i%2) for i,name in enumerate(ids)},
            'oracle_details':{name:{'real':i%2,'selected_trial':0} for i,name in enumerate(ids)},
            'data_sha256':'primitive-hash','generator_version_hash':'frozen-generator',
            'seed':seed,'tier':'T2','real_fraction':.5}


def test_presentation_changes_only_ids_and_hash_with_consistent_bijection(monkeypatch):
    from envs.e3_fdr_adjudication import presentation
    raw=raw_fixture()
    original=copy.deepcopy(raw)
    monkeypatch.setattr(presentation,'raw_make_case',lambda seed,tier:raw)
    result=presentation.make_case(1000000,'T2')
    assert raw == original  # no mutation of shared/cached host data
    before,after=raw['public']['candidates'],result['public']['candidates']
    mapping={left['id']:right['id'] for left,right in zip(before,after,strict=True)}
    assert len(mapping) == len(set(mapping.values())) == 20
    assert set(mapping).isdisjoint(mapping.values())
    for left,right in zip(before,after,strict=True):
        assert {k:v for k,v in left.items() if k!='id'} == {k:v for k,v in right.items() if k!='id'}
    for field in ('truth','effects','oracle_details'):
        assert result[field] == {mapping[name]:value for name,value in raw[field].items()}
    for field in ('generator_version_hash','seed','tier','real_fraction'):
        assert result[field] == raw[field]
    assert result['public']['hypothesis'] == raw['public']['hypothesis']
    encoded=json.dumps(result['public'],sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    assert result['data_sha256'] == hashlib.sha256(encoded).hexdigest()
    assert presentation.make_case(1000000,'T2') == result


def test_presented_ids_do_not_encode_old_id_or_seed_if_public_numerics_identical(monkeypatch):
    from envs.e3_fdr_adjudication import presentation
    monkeypatch.setattr(presentation,'raw_make_case',lambda seed,tier:raw_fixture(seed,'seed-derived-'+str(seed)+'-'))
    one=presentation.make_case(1000000,'T2')
    two=presentation.make_case(1000001,'T2')
    assert one['public'] == two['public']
    assert one['data_sha256'] == two['data_sha256']


def test_identical_candidate_numerics_still_receive_unique_ids_by_position(monkeypatch):
    from envs.e3_fdr_adjudication import presentation
    raw=raw_fixture()
    same={k:v for k,v in raw['public']['candidates'][0].items() if k!='id'}
    for candidate in raw['public']['candidates']:
        old_id=candidate['id']
        candidate.clear()
        candidate.update(copy.deepcopy(same),id=old_id)
    monkeypatch.setattr(presentation,'raw_make_case',lambda seed,tier:raw)
    result=presentation.make_case(1000000,'T2')
    assert len({candidate['id'] for candidate in result['public']['candidates']}) == 20
