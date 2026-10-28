"""Template mutations, AST presentation diversity and public-template auditing."""
import ast
import copy
import inspect
import random
from .catalogue import CATALOGUE, BY_ID
from .reference import research,forward_label,training_report,moment_report


def expression(text, realization):
    if realization%3==0:return text
    helpers={
      'day-1':'(lambda timestamp: timestamp-1)(day)',
      'day+1':'(lambda timestamp: timestamp+1)(day)',
      'day':'(lambda clock: clock)(day)',
      'record[1] <= day':'(lambda report,clock: not(report[1]>clock))(record,day)',
      'record[0] <= day':'(lambda report,clock: not(report[0]>clock))(record,day)',
      'train_end':'(lambda partitions: partitions[1])(data["bounds"])',
      'len(returns)':'(lambda rows: sum(1 for item in rows))(returns)',
      'train_end-horizon':'(lambda boundary,gap: boundary-gap)(train_end,horizon)',
      'fit_end':'(lambda boundary,limit: min(boundary,limit))(fit_end,train_end)',
      'select_end':'(lambda partitions: partitions[2])(data["bounds"])',
      'eval_end':'(lambda partitions: partitions[3])(data["bounds"])',
      'active[day][asset]':'(lambda registry,clock,index: registry[clock][index])(active,day,asset)',
      'active[-1][asset]':'(lambda registry,clock,index: registry[clock][index])(active,-1,asset)',
      'asset':'(lambda stable_id: stable_id)(asset)',
      'ticker_owner[asset]':'(lambda registry,index: registry[index])(ticker_owner,asset)',
      'len(paths)':'(lambda alternatives: sum(1 for item in alternatives))(paths)',
      '1':'(lambda trials: trials)(1)',
    }
    if realization%3==1:return helpers[text]
    # Alternative comparison/control and population/index dataflow forms.
    alternatives={
      'day-1':('day + (-1)','next(t for t in range(day-2,day+1) if t==day-1)'),
      'day+1':('1 + day','next(t for t in range(day,day+3) if t==day+1)'),
      'day':('day + 0','sum(t for t in [day])'),
      'record[1] <= day':('not (record[1] > day)','all(t <= day for t in [record[1]])'),
      'record[0] <= day':('not (record[0] > day)','all(t <= day for t in [record[0]])'),
      'train_end':('data["bounds"][1]','next(v for i,v in enumerate(data["bounds"]) if i==1)'),
      'len(returns)':('returns.__len__()','sum(1 for row in returns)'),
      'train_end-horizon':('train_end + (-horizon)','sum(v for v in [train_end,-horizon])'),
      'fit_end':('min(fit_end,train_end)','next(v for v in [fit_end])'),
      'select_end':('data["bounds"][2]','next(v for i,v in enumerate(data["bounds"]) if i==2)'),
      'eval_end':('data["bounds"][3]','next(v for i,v in enumerate(data["bounds"]) if i==3)'),
      'active[day][asset]':('active.__getitem__(day)[asset]','next(row[asset] for t,row in enumerate(active) if t==day)'),
      'active[-1][asset]':('active.__getitem__(len(active)-1)[asset]','next(row[asset] for t,row in enumerate(active) if t==len(active)-1)'),
      'asset':('int(asset)','next(v for v in [asset])'),
      'ticker_owner[asset]':('ticker_owner.__getitem__(asset)','next(v for i,v in enumerate(ticker_owner) if i==asset)'),
      'len(paths)':('paths.__len__()','sum(1 for path in paths)'),
      '1':('int(True)','sum(v for v in [1])'),
    }
    return alternatives[text][realization%3-1]


def template(mutations=(), realization=0, decoys=True):
    tree=ast.parse(inspect.getsource(research))
    fn=tree.body[0]
    fn.args.args=fn.args.args[:1];fn.args.defaults=[]
    targets={m.target:m for m in CATALOGUE}
    for node in ast.walk(fn):
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            m=targets.get(node.targets[0].id)
            if m:
                text=m.faulty if m.id in mutations else m.clean
                node.value=ast.parse(expression(text,realization),mode='eval').body
    allowed={'F1','F2'} if decoys is True else set(decoys or ())
    for node in ast.walk(fn):
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
            if node.targets[0].id=='labels' and 'F1' not in allowed:
                node.value=ast.parse('training_report(returns,train_start,train_end,horizon)',mode='eval').body
            if node.targets[0].id=='descriptive' and 'F2' not in allowed:
                node.value=ast.parse('moment_report(returns)',mode='eval').body
    return ast.fix_missing_locations(tree)


def render_source(mutations=(), realization=0, presentation_seed=0, decoys=True):
    if set(mutations)-BY_ID.keys(): raise ValueError('unknown mutation')
    tree=template(mutations,realization,decoys)
    rng=random.Random(presentation_seed)
    # Rename every local binding, including comprehension targets and arguments.
    bindings={n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)}
    bindings.add('data')
    bindings.update(n.arg for n in ast.walk(tree) if isinstance(n,ast.arg))
    mapping={name:'v'+''.join(rng.choices('abcdefghijklmnopqrstuvwxyz',k=10)) for name in sorted(bindings)}
    for node in ast.walk(tree):
        if isinstance(node,ast.Name): node.id=mapping.get(node.id,node.id)
        if isinstance(node,ast.arg): node.arg=mapping.get(node.arg,node.arg)
    # Unrelated, independently seeded implementation refactors preserve outputs.
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
            if node.targets[0].id==mapping.get('previous') and rng.randrange(2):
                node.value=ast.parse('[0. for _ in range('+mapping['n']+')]',mode='eval').body if isinstance(node.value,ast.BinOp) else node.value
            if node.targets[0].id==mapping.get('pvalue') and rng.randrange(2):
                class Sqrt(ast.NodeTransformer):
                    def visit_BinOp(self,n):
                        self.generic_visit(n)
                        if isinstance(n.op,ast.Pow) and isinstance(n.left,ast.Constant) and n.left.value==2 and isinstance(n.right,ast.Constant) and n.right.value==.5:
                            return ast.Call(func=ast.Attribute(value=ast.Name(id='math',ctx=ast.Load()),attr='sqrt',ctx=ast.Load()),args=[ast.Constant(2)],keywords=[])
                        return n
                node.value=Sqrt().visit(node.value)
    tree=ast.fix_missing_locations(tree)
    tree.body[0].name='run_research'
    source='import math, json, sys\n'+inspect.getsource(forward_label)+'\n'+inspect.getsource(training_report)+'\n'+inspect.getsource(moment_report)+'\n'+ast.unparse(tree)+'\n'
    if presentation_seed%2:
        source='\n'.join(line+' '*(i%3) for i,line in enumerate(source.splitlines()))+'\n'
    source+='print(json.dumps(run_research(json.load(open(sys.argv[1]))),allow_nan=False))\n'
    return source


def canonical_function(source):
    tree=ast.parse(source)
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and any(isinstance(k,ast.Constant) and k.value=='holdings' for k in ast.walk(n)))
    clean=template().body[0]
    def targets(node):
        return [n.targets[0].id for n in ast.walk(node) if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)]
    original,standard=targets(fn),targets(clean)
    if len(original)!=len(standard): raise ValueError('outside supported public-template domain')
    mapping=dict(zip(original,standard));mapping[fn.args.args[0].arg]='data'
    def binding_names(f):
        names=[]
        for node in ast.walk(f):
            target=node.targets[0] if isinstance(node,ast.Assign) else node.target if isinstance(node,ast.For) else None
            if target is not None:names.extend(n.id for n in ast.walk(target) if isinstance(n,ast.Name))
        return names
    for a,b in zip(binding_names(fn),binding_names(clean)):mapping.setdefault(a,b)
    for n in ast.walk(fn):
        if isinstance(n,ast.Name):n.id=mapping.get(n.id,n.id)
    return fn


def normalized(node):
    node=copy.deepcopy(node)
    bound={}
    for n in ast.walk(node):
        if isinstance(n,ast.Lambda):
            for arg in n.args.args:bound.setdefault(arg.arg,'bound'+str(len(bound)))
        if isinstance(n,ast.comprehension):
            for target in ast.walk(n.target):
                if isinstance(target,ast.Name):bound.setdefault(target.id,'bound'+str(len(bound)))
    for n in ast.walk(node):
        if isinstance(n,ast.Name):n.id=bound.get(n.id,n.id)
        if isinstance(n,ast.arg):n.arg=bound.get(n.arg,n.arg)
    return ast.dump(node,include_attributes=False)


def source_locations(source):
    fn=canonical_function(source)
    found={}
    for node in ast.walk(fn):
        if not isinstance(node,ast.Assign) or not isinstance(node.targets[0],ast.Name):continue
        for m in CATALOGUE:
            if node.targets[0].id!=m.target:continue
            for r in range(3):
                candidate=ast.parse(expression(m.faulty,r),mode='eval').body
                if normalized(node.value)==normalized(candidate):
                    found[m.id]=(node.lineno,node.end_lineno)
    return found


def audit(source):
    # The solver receives all template grammar, never case-specific ground truth.
    locations=source_locations(source)
    return [{'family':BY_ID[k].family,'line':v[0]} for k,v in locations.items()]
