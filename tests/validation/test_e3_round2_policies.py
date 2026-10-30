"""Policy-source contracts; do not execute until screen is committed."""
import importlib.util
from pathlib import Path


def policies():
    path = Path(__file__).with_name('e3_round2_policies.py')
    spec = importlib.util.spec_from_file_location('independent_e3_policies', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_declared_roster_and_sources_compile_without_running():
    module = policies()
    assert len(module.WRONG_POLICIES) >= 12
    assert len(set(module.WRONG_POLICIES)) == len(module.WRONG_POLICIES)
    assert len(module.CHEATER_POLICIES) == 8
    for mode in module.WRONG_POLICIES+module.CHEATER_POLICIES+('oracle','honest','shallow','random'):
        source = module.submitted_source(mode, {'example_id':1})
        compile(source, '<independent-e3-policy>', 'exec')


def test_hardcoded_ids_source_snapshots_public_honest_answer_before_replay():
    """Source contract only; does not execute a policy or access /work."""
    import ast
    source=policies().submitted_source('hardcoded_ids')
    tree=ast.parse(source)
    assert "probability_vectors(public, 'honest')" in source
    writes=[node for node in ast.walk(tree) if isinstance(node,ast.Call)
            and isinstance(node.func,ast.Name) and node.func.id=='open'
            and len(node.args)>=2 and isinstance(node.args[0],ast.Constant)
            and node.args[0].value=='/work/program.py'
            and isinstance(node.args[1],ast.Constant) and node.args[1].value=='w']
    assert len(writes)==1
    assert 'fixed_source' in source
    assert 'print(json.dumps(snapshot))' in source
    assert '/opt/qi/private' not in source
