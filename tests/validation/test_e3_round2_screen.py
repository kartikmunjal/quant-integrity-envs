"""Pure screen plumbing mocks; no actual seed construction or policy execution."""
import importlib.util
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[2]/'scripts/p3b2_screen.py'
    spec = importlib.util.spec_from_file_location('independent_screen_test',path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_screen_keeps_every_rejection_and_stops_at_declared_target(monkeypatch):
    screen = module()
    def fake_inspect(seed):
        if seed in (1000000,1000002): raise ValueError('fixture structural rejection')
        return {'T1':'fixture'}
    monkeypatch.setattr(screen,'inspect_seed',fake_inspect)
    result = screen.screen(1000000,1000009,target=2)
    assert result['admissible'] == [1000001,1000003]
    assert [row['seed'] for row in result['rejected']] == [1000000,1000002]
    assert result['inspected_count'] == 4
    assert result['rejected_count'] == 2
    assert result['inspected_through'] == 1000003
    assert result['target_met']
    assert set(result['public_hashes']) == {'1000001','1000003'}


def test_screen_reports_unmet_target_without_dropping_failures(monkeypatch):
    screen = module()
    def reject(seed): raise ValueError('fixture no candidate')
    monkeypatch.setattr(screen,'inspect_seed',reject)
    result = screen.screen(1000000,1000002,target=2)
    assert not result['target_met']
    assert result['admissible'] == []
    assert len(result['rejected']) == result['inspected_count'] == 3


def test_inspect_requires_mixed_twenty_candidate_structure(monkeypatch):
    screen = module()
    monkeypatch.setattr(screen,'make_case',lambda seed,tier:{'public':{'candidates':[]},'truth':{}})
    with pytest.raises(ValueError,match='membership'):
        screen.inspect_seed(1000000)


def test_screen_module_does_not_import_policies_or_rewards():
    path = Path(__file__).resolve().parents[2]/'scripts/p3b2_screen.py'
    import ast
    tree = ast.parse(path.read_text())
    imports = [node.module or '' for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
    imports += [name.name for node in ast.walk(tree) if isinstance(node,ast.Import) for name in node.names]
    assert not any('polic' in name or 'reward' in name for name in imports)
