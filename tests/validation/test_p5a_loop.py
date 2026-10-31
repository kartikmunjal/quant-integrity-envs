"""Independent host loop limits and submission control, with fake model replies."""
import asyncio


class FakeTools:
    def __init__(self): self.submitted=False;self.terminal=False;self.reason='';self.calls=[]
    async def dispatch(self,name,arguments):
        self.calls.append((name,arguments))
        if name=='submit': self.submitted=True
        return {'ok':True,'output':'fixture','terminal':False,'truncated':False}


def test_non_submitting_model_stops_at_turn_limit_with_defined_zero():
    from qi_harness.client import MockClient,Reply
    from qi_harness.config import Limits
    from qi_harness.harness import run_loop
    tools=FakeTools()
    result=asyncio.run(run_loop(MockClient([Reply(content='continue',input_tokens=2,output_tokens=1)]*5),tools,
                               Limits(max_turns=3)))
    assert result['reason']=='max_turns' and result['reward']==0
    assert not result['submitted'] and result['turns']==3
    assert result['total_tokens']==9


def test_token_limit_stops_before_another_model_request():
    from qi_harness.client import Reply
    from qi_harness.config import Limits
    from qi_harness.harness import run_loop
    class Client:
        calls=0
        async def complete(self,messages,tools,max_completion_tokens):
            self.calls+=1
            assert max_completion_tokens<=4
            return Reply(content='fixture',input_tokens=3,output_tokens=2)
    client=Client()
    result=asyncio.run(run_loop(client,FakeTools(),Limits(max_total_tokens=4,max_completion_tokens=4)))
    assert result['reward']==0 and result['reason']=='max_total_tokens' and client.calls==1
    assert result['total_tokens']==5  # already observed usage is never discarded


def test_wall_timeout_is_defined_zero_without_submission():
    from qi_harness.config import Limits
    from qi_harness.harness import run_loop
    class Client:
        async def complete(self,*args,**kwargs): await asyncio.sleep(.2)
    result=asyncio.run(run_loop(Client(),FakeTools(),Limits(wall_seconds=.01)))
    assert result['reward']==0 and result['reason']=='wall_timeout' and not result['submitted']


def test_tool_calls_execute_sequentially_and_submit_ends_the_loop():
    from qi_harness.client import MockClient,Reply,ToolCall
    from qi_harness.config import Limits
    from qi_harness.harness import run_loop
    tools=FakeTools()
    reply=Reply(tool_calls=(ToolCall('1','list_files',{}),ToolCall('2','run_python',{'code':'fixture'}),
                            ToolCall('3','submit',{'source':'fixture source'})),input_tokens=3,output_tokens=4)
    result=asyncio.run(run_loop(MockClient([reply]),tools,Limits()))
    assert [name for name,args in tools.calls]==['list_files','run_python','submit']
    assert result['reason']=='submitted' and result['submitted']
    assert result['input_tokens']==3 and result['output_tokens']==4


def test_over_budget_reply_cannot_submit_before_token_guard():
    from qi_harness.client import MockClient,Reply,ToolCall
    from qi_harness.config import Limits
    from qi_harness.harness import run_loop
    tools=FakeTools()
    reply=Reply(tool_calls=(ToolCall('submit','submit',{'source':'inert fixture'}),),
                input_tokens=3,output_tokens=2)
    result=asyncio.run(run_loop(MockClient([reply]),tools,Limits(max_total_tokens=4,max_completion_tokens=4)))
    assert result['reason']=='max_total_tokens' and result['reward']==0
    assert not result['submitted'] and tools.calls==[]


def test_provider_cannot_exceed_per_turn_completion_cap_and_then_execute_tools():
    from qi_harness.client import MockClient,Reply,ToolCall
    from qi_harness.config import Limits
    from qi_harness.harness import run_loop
    tools=FakeTools()
    reply=Reply(tool_calls=(ToolCall('submit','submit',{'source':'inert fixture'}),),input_tokens=0,output_tokens=5)
    result=asyncio.run(run_loop(MockClient([reply]),tools,Limits(max_completion_tokens=4)))
    assert result['reason']=='max_completion_tokens' and result['reward']==0
    assert not result['submitted'] and tools.calls==[]
