"""Identity-only solver presentation without a directly seed-encoded ID."""
import copy
from .cases import make_case as raw_make_case, digest


def make_case(seed,tier):
    raw=raw_make_case(seed,tier)
    result=copy.deepcopy(raw)
    mapping={}
    for position,candidate in enumerate(result['public']['candidates']):
        old=candidate.pop('id')
        new='strategy-'+digest({'position':position,'visible':candidate})[:24]
        if new in mapping.values():
            raise ValueError('candidate identity collision')
        mapping[old]=new
        candidate['id']=new
    for key in ('truth','effects','oracle_details'):
        result[key]={mapping[name]:value for name,value in result[key].items()}
    result['primitive_data_sha256']=raw['data_sha256']
    result['data_sha256']=digest(result['public'])
    return result
