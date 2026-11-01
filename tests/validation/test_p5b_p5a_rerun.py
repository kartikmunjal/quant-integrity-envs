"""Pure parent-population immutability contracts; no policy or Docker imports."""
import importlib.util
from pathlib import Path
import pytest


def module():
    path=Path(__file__).with_name('p5b_p5a_rerun.py')
    spec=importlib.util.spec_from_file_location('p15_envelope_contract',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def test_envelope_allows_only_execution_source_update():
    m=module();parent={'mode':'boundary','concurrency':8,'windows_path':'fixture',
                      'window_manifest_sha256':'fixture','rows':[{'seed':1002500}],'sources':{'old':'hash'}}
    m.validate_parent(parent,dict(parent,sources={'new':'hash'}))


@pytest.mark.parametrize('change',[{'mode':'stress'},{'concurrency':12},{'rows':[{'seed':1002501}]},
                                    {'windows_path':'other'},{'window_manifest_sha256':'other'}])
def test_envelope_rejects_any_population_or_execution_scale_change(change):
    m=module();parent={'mode':'boundary','concurrency':8,'windows_path':'fixture',
                      'window_manifest_sha256':'fixture','rows':[{'seed':1002500}],'sources':{}}
    with pytest.raises(ValueError):m.validate_parent(parent,dict(parent,**change))
