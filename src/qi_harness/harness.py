"""Host model/tool loop; task rewards remain in unchanged environment verifiers."""
import asyncio
import json
import time


async def run_loop(client,tools,limits):
    started=time.monotonic();messages=list(getattr(tools,'initial_messages',[]))
    result={'submitted':False,'reward':0.,'reason':'max_turns','turns':0,'input_tokens':0,'output_tokens':0,'total_tokens':0,'messages':messages}
    redact=getattr(client,'redact',lambda value:value)
    def finish(reason):
        result.update(reason=reason,submitted=bool(tools.submitted),wall_seconds=time.monotonic()-started)
        if reason!='submitted' and hasattr(tools,'runtime'):tools.runtime.flagged=True
        return result
    async def body():
        for turn in range(limits.max_turns):
            remaining=limits.max_total_tokens-result['total_tokens']
            if remaining<=0:return finish('max_total_tokens')
            maximum=min(remaining,limits.max_completion_tokens)
            try:reply=await client.complete(messages,getattr(tools,'schemas',[]),max_completion_tokens=maximum)
            except (RuntimeError,ValueError):return finish('client_error')
            result['turns']=turn+1;result['input_tokens']+=reply.input_tokens;result['output_tokens']+=reply.output_tokens
            result['total_tokens']=result['input_tokens']+result['output_tokens']
            if getattr(client,'stop_required',False):return finish('budget_stop')
            if result['total_tokens']>limits.max_total_tokens:return finish('max_total_tokens')
            if reply.output_tokens>maximum:return finish('max_completion_tokens')
            if len(reply.tool_calls)>16:return finish('tool_call_limit')
            assistant={'role':'assistant','content':reply.content,'tool_calls':[{'id':c.id,'type':'function','function':{'name':c.name,'arguments':json.dumps(c.arguments,allow_nan=False)}} for c in reply.tool_calls]}
            messages.append(redact(assistant))
            if len(json.dumps(messages,allow_nan=False).encode())>limits.transcript_bytes:return finish('transcript_limit')
            for call in reply.tool_calls:
                output=await tools.dispatch(call.name,call.arguments)
                messages.append(redact({'role':'tool','tool_call_id':call.id,'content':json.dumps(output,allow_nan=False)}))
                if len(json.dumps(messages,allow_nan=False).encode())>limits.transcript_bytes:return finish('transcript_limit')
                if tools.terminal:return finish(tools.reason or 'tool_failure')
                if tools.submitted:return finish('submitted')
        return finish('max_turns')
    try:
        async with asyncio.timeout(limits.wall_seconds):return await body()
    except TimeoutError:return finish('wall_timeout')
