"""E6 source policies and replay over the shared checked Docker runtime."""
import hashlib
import inspect
from qi_runtime import CheckedRuntime,WORK,PRIVATE,IMAGE,MAX_SOURCE,execute_program
from .repair import reconstruct
from .reward import check_answer


def reference_program(mode='exact'):
    return inspect.getsource(reconstruct)+'\nimport json,sys\nx=json.load(open(sys.argv[1]))\nresult=reconstruct(x,'+repr(mode)+')\nprint(json.dumps(result))\n'


def replay_seed(seed,tier,source):
    start=1007000 if seed<1008000 else 1009000
    value=start+int.from_bytes(hashlib.sha256(f'E6:{seed}:{tier}:{source}'.encode()).digest()[:8],'big')%1000
    return start+(value-start+1)%1000 if value==seed else value


async def execute_once(data,program):
    return await execute_program(data,program,lambda output:check_answer(output,data),namespace='e6')
