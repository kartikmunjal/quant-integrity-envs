"""P15 source-version envelope around the unchanged independent P14 driver.

Parent plan bytes/rows remain unchanged. Only the execution-source binding is
renewed prospectively; all operations, criteria and comparisons are inherited.
"""
import argparse
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def validate_parent(parent,current):
    for key in ('mode','concurrency','windows_path','window_manifest_sha256','rows'):
        if parent[key]!=current[key]:raise ValueError('parent population/criterion drift: '+key)


def driver(parent_path):
    parent_path=Path(parent_path)
    if parent_path.is_absolute():parent_path=parent_path.relative_to(ROOT)
    parent_raw=(ROOT/parent_path).read_bytes();parent=json.loads(parent_raw)
    committed=subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:'+str(parent_path)])
    if parent_raw!=committed:raise ValueError('parent plan must remain committed byte-identical')
    path=Path(__file__).with_name('p5a_docker_validation.py')
    spec=importlib.util.spec_from_file_location('independent_p14_driver_for_p15',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    original_sources=module.execution_sources
    def execution_sources():
        return {**original_sources(),str(Path(__file__).relative_to(ROOT)):sha(Path(__file__).read_bytes())}
    module.execution_sources=execution_sources
    original_make=module.make_execution_plan
    def make_execution_plan(mode,window_path,concurrency):
        envelope=original_make(mode,window_path,concurrency)
        validate_parent(parent,envelope)
        envelope['parent_plan']={'path':str(parent_path),'sha256':sha(parent_raw),
                                 'kind':'unchanged P14 cohort; P15 execution-source envelope only'}
        return envelope
    module.make_execution_plan=make_execution_plan
    return module


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=('boundary','environment-data','equivalence','stress'))
    parser.add_argument('--parent-plan',required=True);parser.add_argument('--windows',required=True)
    parser.add_argument('--output',required=True);parser.add_argument('--concurrency',type=int,default=8)
    parser.add_argument('--write-plan',action='store_true');parser.add_argument('--confirm-mock-docker',action='store_true')
    args=parser.parse_args();module=driver(args.parent_plan)
    if args.write_plan:
        plan=module.make_execution_plan(args.mode,args.windows,args.concurrency)
        path=Path(args.output).with_name(Path(args.output).stem+'_plan.json')
        with path.open('xb') as stream:stream.write(module.canonical(plan)+b'\n')
        print('Commit '+str(path)+' before execution.');raise SystemExit(0)
    if not args.confirm_mock_docker:raise SystemExit('explicit mock Docker authorization required')
    result=asyncio.run(module.run(args.mode,args.windows,args.output,args.concurrency))
    print(json.dumps({k:result[k] for k in ('mode','rows','failed_rows','retries','passed')}))
    raise SystemExit(0 if result['passed'] else 1)
