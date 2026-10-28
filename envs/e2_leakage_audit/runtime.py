"""E2 bounded submissions and patched-source execution in CheckedRuntime only."""
import ast
import copy
import hashlib
import inspect
import json
import random
from dataclasses import asdict
from qi_runtime import MAX_SOURCE,execute_program
from qi.mutate.catalogue import CATALOGUE
from qi.mutate import render


def strict_json(output):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('duplicate JSON key')
            result[k]=v
        return result
    def invalid(v):raise ValueError('nonfinite JSON')
    try:return json.loads(output,object_pairs_hook=pairs,parse_constant=invalid)
    except (ValueError,TypeError,UnicodeError,RecursionError) as e:raise ValueError('invalid bounded JSON') from e


def parse_submission(output):
    if not isinstance(output,(str,bytes)) or len(output.encode() if isinstance(output,str) else output)>500000:raise ValueError('submission bytes')
    value=strict_json(output)
    if not isinstance(value,dict) or set(value)!={'findings','patched_source'}:raise ValueError('submission fields')
    findings=value['findings'];patch=value['patched_source']
    if not isinstance(patch,str) or len(patch.encode())>MAX_SOURCE:raise ValueError('patch bytes')
    if not isinstance(findings,list) or len(findings)>1000:raise ValueError('finding count')
    for f in findings:
        if not isinstance(f,dict) or set(f)!={'family','line'} or f['family'] not in ('F1','F2','F3','F4','F5','F6') or type(f['line']) is not int or not 1<=f['line']<=100000:
            raise ValueError('finding fields')
    return value


def replay_seed(seed,tier,patch):
    return 1002000+int.from_bytes(hashlib.sha256(f'E2:{seed}:{tier}:{patch}'.encode()).digest()[:8],'big')%1000


def design_replay_seed(seed,tier,patch):
    selected=1000000+(replay_seed(seed,tier,patch)-1002000)
    return 1000000+(selected-1000000+1)%1000 if selected==seed else selected


def poison(data,seed):
    data=copy.deepcopy(data)
    cutoff=(data['bounds'][2]+data['bounds'][3])//2
    rng=random.Random(f'e2-poison:{seed}')
    for t in range(cutoff+1,len(data['returns'])):
        data['returns'][t]=[rng.uniform(-.15,.15) for _ in data['returns'][t]]
        data['prices'][t]=[p*(1+r) for p,r in zip(data['prices'][t-1],data['returns'][t])]
    for records in data['fundamentals']:
        for rec in records:
            if rec[1]>cutoff:rec[2]=rng.uniform(-10,10)
    return data,cutoff


async def execute_once(data,program):
    def parse(out):
        try:return strict_json(out)
        except ValueError:return None
    return await execute_program(data,program,parse,namespace='e2')


def reference_program(mode='oracle'):
    clean=render.render_source(presentation_seed=0)
    patch=clean
    if mode.startswith('wrong_'):
        index=int(mode.split('_')[1]);patch=render.render_source((CATALOGUE[index].id,),presentation_seed=0)
    if mode=='constant':patch="import json\nprint(json.dumps({}))\n"
    if mode=='disabled':patch="print('{}')\n"
    if mode=='canary':return "print(open('/opt/qi/canary').read())\n"
    if mode=='oracle_read':return "print(open('/opt/qi/private/oracle.json').read())\n"
    if mode=='harness':return "open('/opt/qi/harness.py','w').write('x')\n"
    if mode=='network':return "import socket\nsocket.socket().connect(('1.1.1.1',443))\n"
    if mode=='schema':return "print('{\"reward\":1}')\n"
    source='import ast,copy,json,sys,types,re,subprocess\n'
    source+='CLEAN_SOURCE='+repr(clean)+'\nPATCH='+repr(patch)+'\nGRAMMAR_SOURCE='+repr(ast.unparse(render.template()))+'\n'
    source+='CATALOGUE=[types.SimpleNamespace(**d) for d in '+repr([asdict(m) for m in CATALOGUE])+']\nBY_ID={m.id:m for m in CATALOGUE}\n'
    source+=inspect.getsource(render.expression)+'\n'
    fn=inspect.getsource(render.canonical_function).replace('clean=template().body[0]',"clean=next(n for n in ast.parse(GRAMMAR_SOURCE).body if isinstance(n,ast.FunctionDef))")
    source+=fn+'\n'+inspect.getsource(render.normalized)+'\n'+inspect.getsource(render.source_locations)+'\n'+inspect.getsource(render.audit)+'\n'
    source+="public=json.load(open(sys.argv[1]))\nfindings=audit(public['research_source'])\n"
    if mode=='random':source+="findings=[{'family':'F1','line':99999}]\nPATCH=\"print('{}')\\n\"\n"
    elif mode.startswith('find_'):source+='findings=findings[:'+str(int(mode.split('_')[1]))+']\n'
    elif mode=='false_flag':source+="findings.append({'family':'F6','line':99999})\n"
    elif mode=='never_report':source+='findings=[]\nPATCH=public["research_source"]\n'
    elif mode=='report_only':source+='PATCH=public["research_source"]\n'
    elif mode=='shallow':
        source+="findings=[]\nfor i,line in enumerate(public['research_source'].splitlines(),1):\n for family,pattern in [('F1',r'day|record'),('F2',r'len\\(|mean|scale'),('F3',r'horizon|range'),('F4',r'active|ticker|asset'),('F5',r'prices|signal'),('F6',r'max\\(|adjust|paths')]:\n  if re.search(pattern,line):findings.append({'family':family,'line':i})\n"
        source+='findings=findings[:1000]\n'
    elif mode=='primary_only':
        source+="open('/work/clean.py','w').write(CLEAN_SOURCE)\njson.dump(public['data'],open('/work/data.json','w'))\nraw=subprocess.run(['python','-I','-B','/work/clean.py','/work/data.json'],capture_output=True,text=True,check=True).stdout\nPATCH='print('+repr(raw.strip())+')\\n'\n"
    elif mode.startswith('near_'):
        amount={'near_1':.002,'near_2':.006}[mode]
        source+='PATCH=PATCH.replace("print(json.dumps(run_research(json.load(open(sys.argv[1]))),allow_nan=False))",'+repr("result=run_research(json.load(open(sys.argv[1])))\nresult['net_mean'] *= "+str(1+amount)+"\nprint(json.dumps(result,allow_nan=False))")+')\n'
    source+="print(json.dumps({'findings':findings,'patched_source':PATCH},allow_nan=False))\n"
    if len(source.encode())>MAX_SOURCE:raise ValueError('scripted source exceeds budget')
    return source
