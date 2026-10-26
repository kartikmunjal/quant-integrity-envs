"""Read only this project's GitHub Actions status; never print or persist auth."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

BASE='https://api.github.com/repos/kartikmunjal/Quant-fin-agent'


def _get(path,token):
    headers={'Accept':'application/vnd.github+json','User-Agent':'quant-integrity-envs-ci-check'}
    if token:headers['Authorization']='Bearer '+token
    with urllib.request.urlopen(urllib.request.Request(BASE+path,headers=headers),timeout=30) as response:
        return json.load(response)


def check(sha):
    token=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    record={'repository':'kartikmunjal/Quant-fin-agent','head_sha':sha,'checked_utc':datetime.now(timezone.utc).isoformat(),'authenticated':bool(token),'runs':[]}
    try:
        payload=_get('/actions/runs?per_page=50&head_sha='+sha,token)
        for run in payload.get('workflow_runs',[]):
            if run.get('head_sha')!=sha or run.get('name')!='CI':continue
            saved={key:run.get(key) for key in ('id','head_sha','name','status','conclusion','html_url')}
            saved['jobs']=[]
            jobs=_get('/actions/runs/'+str(run['id'])+'/jobs?per_page=100',token)
            for job in jobs.get('jobs',[]):
                saved['jobs'].append({key:job.get(key) for key in ('id','name','status','conclusion','html_url')} | {'steps':[{key:step.get(key) for key in ('name','status','conclusion')} for step in job.get('steps',[])]})
            record['runs'].append(saved)
        if not record['runs']:record['result']='no_matching_run'
        elif any(run['status']!='completed' for run in record['runs']):record['result']='pending'
        elif all(run['conclusion']=='success' and run['jobs'] and all(j['conclusion']=='success' for j in run['jobs']) for run in record['runs']):record['result']='pass'
        else:record['result']='fail'
    except urllib.error.HTTPError as error:
        record.update(result='unavailable',http_code=error.code)
    except urllib.error.URLError:
        record.update(result='unavailable',reason='network request failed')
    return record


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sha',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
    if len(args.sha)!=40 or any(c not in '0123456789abcdef' for c in args.sha):raise ValueError('full commit SHA required')
    record=check(args.sha)
    Path(args.output).write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    print(json.dumps(record,indent=2))
    return 0 if record['result']=='pass' else 2 if record['result']=='unavailable' else 1

if __name__=='__main__':raise SystemExit(main())
