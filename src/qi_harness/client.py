"""Small compatible chat protocol with a fail-closed P5a provider lock."""
import asyncio
from dataclasses import dataclass
import json
import os
import re
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass(frozen=True)
class Reply:
    content: str = ''
    tool_calls: tuple = ()
    input_tokens: int = 0
    output_tokens: int = 0

    def __post_init__(self):
        if any(type(x) is not int or x < 0 for x in (self.input_tokens,self.output_tokens)):
            raise ValueError('invalid token usage')


@dataclass(frozen=True)
class ClientConfig:
    base_url: str
    model: str
    key_env_name: str
    allow_loopback_test: bool = False
    dry_run: bool = False

    def __post_init__(self):
        u=urlsplit(self.base_url)
        if u.scheme not in ('http','https') or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError('invalid base URL')
        if not self.model or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',self.key_env_name):
            raise ValueError('model and key variable NAME required')


def read_key(name):
    """Call-time only. Provider lock must be checked before invoking this helper."""
    value=os.environ.get(name)
    if not value:raise RuntimeError('configured credential is unavailable')
    return value


class MockClient:
    def __init__(self,replies):
        self.replies=iter(replies)
        self.calls=0

    async def complete(self,messages,tools,*,max_completion_tokens):
        try:result=next(self.replies)
        except StopIteration:raise RuntimeError('mock replies exhausted') from None
        self.calls+=1
        return result


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise RuntimeError('redirect refused')


class CompatibleClient:
    def __init__(self,config,budget=None):
        self.config=config
        self.budget=budget
        self.stop_required=False
        self.usage_unknown=False
        self._secrets=[]
        if config.allow_loopback_test:
            u=urlsplit(config.base_url)
            if u.scheme!='http' or u.hostname not in ('127.0.0.1','::1'):
                raise ValueError('test transport requires literal loopback HTTP')
            if not config.key_env_name.startswith('P5A_FAKE_'):
                raise ValueError('loopback tests require a deliberately fake key variable')

    def redact(self,value):
        if isinstance(value,str):
            for secret in self._secrets:value=value.replace(secret,'[REDACTED]')
            return value
        if isinstance(value,list):return [self.redact(v) for v in value]
        if isinstance(value,dict):return {self.redact(k):self.redact(v) for k,v in value.items()}
        return value

    async def complete(self,messages,tools,*,max_completion_tokens):
        if self.config.dry_run:return Reply(content='dry-run: no credential lookup or connection')
        if not self.config.allow_loopback_test:
            raise RuntimeError('P5a provider calls locked; owner authorization in a later phase is required')
        if type(max_completion_tokens) is not int or max_completion_tokens<=0:
            raise ValueError('positive completion limit required')
        body={'model':self.config.model,'messages':messages,'tools':tools,
              'max_completion_tokens':max_completion_tokens,'stream':False}
        raw=json.dumps(body,allow_nan=False).encode()
        if len(raw)>2_097_152:raise ValueError('request exceeds bound')
        if self.budget is None:raise ValueError('priced budget authorization required')
        # This transport is loopback-test-only. A later provider integration must
        # validate its token upper-bound contract before unlocking paid dispatch.
        reservation=self.budget.reserve(self.config.model,len(raw)+4096,max_completion_tokens)
        try:key=read_key(self.config.key_env_name)
        except BaseException:
            self.budget.cancel(reservation);raise
        self._secrets.append(key)
        def request():
            # No proxy/environment discovery, redirects, retries or provider SDK.
            opener=build_opener(ProxyHandler({}),_NoRedirect())
            req=Request(self.config.base_url.rstrip('/')+'/chat/completions',data=raw,
                        headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
            try:
                with opener.open(req,timeout=20) as response:
                    data=response.read(2_097_153)
                if len(data)>2_097_152:raise RuntimeError('bounded response exceeded')
                return json.loads(data)
            except Exception:
                raise RuntimeError('compatible test transport failed; response/headers omitted') from None
        try:data=await asyncio.to_thread(request)
        except BaseException:
            self.usage_unknown=True
            self.budget.uncertain(reservation);raise
        try:
            usage=data['usage']
            decision=self.budget.settle(reservation,usage['prompt_tokens'],usage['completion_tokens'])
            self.stop_required=decision.stop_required
        except (KeyError,TypeError,ValueError):
            self.usage_unknown=True
            self.budget.uncertain(reservation)
            raise RuntimeError('response usage missing; budget reconciliation required') from None
        try:
            message=self.redact(data['choices'][0]['message']);usage=data['usage']
            calls=[]
            for call in message.get('tool_calls',[]):
                function=call['function'];arguments=json.loads(function['arguments'])
                if not isinstance(arguments,dict):raise ValueError('object tool arguments required')
                calls.append(ToolCall(call['id'],function['name'],arguments))
            return Reply(content=message.get('content') or '',tool_calls=tuple(calls),
                         input_tokens=usage['prompt_tokens'],output_tokens=usage['completion_tokens'])
        except (KeyError,TypeError,ValueError):
            raise RuntimeError('invalid bounded compatible response') from None
