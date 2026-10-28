"""Source-bound full-suite proof with bounded original-preserving JUnit output."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.run_p3a_gate import source_files
from scripts.p3a_support import canonical,sha,ensure_tracked_capacity
from scripts.compact_junit import compact


def main():
    path=ROOT/'results/p3a_tests.json'
    if path.exists():raise ValueError('full-suite proof already exists')
    started=time.monotonic();versions=source_files();junit=ROOT/'logs/p3a_final_tests.xml'
    env=dict(os.environ,QI_REAL_SANDBOX='1')
    with (ROOT/'logs/p3a_final_tests_console.txt').open('x') as stream:
        code=subprocess.call([str(ROOT/'.venv/bin/python'),'-m','pytest','--junitxml='+str(junit)],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
    original=compact(junit,ROOT/'artifacts/p3a/development/junit-originals') if junit.exists() else None
    if original:original['path']=str(Path(original['path']).relative_to(ROOT));original['original_path']=str(junit.relative_to(ROOT))
    tree=ET.parse(junit);suites=tree.getroot().findall('testsuite')
    counts={key:sum(int(s.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
    result={'host_python':sys.version,'sources':versions,'exit_code':code,'counts':counts,'passed':code==0 and not counts['failures'] and not counts['errors'] and counts['tests']>=468 and source_files()==versions,
            'junit_path':str(junit.relative_to(ROOT)),'junit_sha256':sha(junit.read_bytes()),'original_archive':original,
            'wall_seconds':time.monotonic()-started,'api_spend_usd':0,'gpu_spend_usd':0}
    ensure_tracked_capacity(len(canonical(result))+1);path.write_bytes(canonical(result)+b'\n');print(json.dumps({k:result[k] for k in ('passed','counts','wall_seconds')}))
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
