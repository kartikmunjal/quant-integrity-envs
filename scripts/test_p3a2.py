"""Source-bound full-suite proof with bounded original-preserving JUnit output."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.run_p3a2 import source_files
from scripts.p3a2_support import canonical,sha,ensure_tracked_capacity
from scripts.compact_junit import compact


def main(result_name,junit_name,console_name):
    path=ROOT/'results'/(result_name+'.json')
    if path.exists():raise ValueError('full-suite proof already exists')
    started=time.monotonic();versions=source_files();junit=ROOT/'logs'/junit_name
    env=dict(os.environ,QI_REAL_SANDBOX='1')
    with (ROOT/'logs'/console_name).open('x') as stream:
        code=subprocess.call([str(ROOT/'.venv/bin/python'),'-m','pytest','--junitxml='+str(junit)],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
    original=compact(junit,ROOT/'artifacts/p3a2/development/junit-originals') if junit.exists() else None
    if original:original['path']=str(Path(original['path']).relative_to(ROOT));original['original_path']=str(junit.relative_to(ROOT))
    tree=ET.parse(junit);suites=tree.getroot().findall('testsuite')
    counts={key:sum(int(s.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
    result={'host_python':sys.version,'sources':versions,'exit_code':code,'counts':counts,'passed':code==0 and not counts['failures'] and not counts['errors'] and counts['tests']>=509 and not counts['skipped'] and source_files()==versions,
            'junit_path':str(junit.relative_to(ROOT)),'junit_sha256':sha(junit.read_bytes()),'original_archive':original,
            'wall_seconds':time.monotonic()-started,'api_spend_usd':0,'gpu_spend_usd':0}
    ensure_tracked_capacity(len(canonical(result))+1);path.write_bytes(canonical(result)+b'\n');print(json.dumps({k:result[k] for k in ('passed','counts','wall_seconds')}))
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--result-name',default='p3a2_tests');parser.add_argument('--junit-name',default='p3a2_final_tests.xml');parser.add_argument('--console-name',default='p3a2_final_tests_console.txt')
    args=parser.parse_args()
    if any(Path(v).name!=v or not v.startswith('p3a') for v in vars(args).values()):parser.error('phase basenames only')
    main(args.result_name,args.junit_name,args.console_name)
