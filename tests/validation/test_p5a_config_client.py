"""Independent P5a contracts; no remote model calls or real key reads."""
import asyncio
import json
import socket

import pytest


def test_committed_default_limits_and_invalid_limits():
    from qi_harness.config import Limits
    limits=Limits()
    assert (limits.max_turns,limits.max_completion_tokens,limits.max_total_tokens,
            limits.wall_seconds,limits.tool_output_bytes,limits.transcript_bytes)==(
                16,2048,32768,180,16384,2097152)
    for name in ('max_turns','max_completion_tokens','max_total_tokens','wall_seconds',
                 'tool_output_bytes','transcript_bytes'):
        with pytest.raises(ValueError): Limits(**{name:0})
    with pytest.raises(ValueError): Limits(max_turns=True)


def test_mock_reply_and_tool_call_interface_is_deterministic():
    from qi_harness.client import MockClient,Reply,ToolCall
    first=Reply(content='analysis fixture',tool_calls=(ToolCall('one','list_files',{}),),input_tokens=7,output_tokens=3)
    second=Reply(content='done',input_tokens=9,output_tokens=1)
    client=MockClient([first,second])
    async def scenario():
        assert await client.complete([],[],max_completion_tokens=20)==first
        assert await client.complete([],[],max_completion_tokens=20)==second
        with pytest.raises(RuntimeError,match='exhaust'): await client.complete([],[],max_completion_tokens=20)
    asyncio.run(scenario())


def test_remote_lock_precedes_key_lookup_or_socket(monkeypatch):
    from qi_harness import client as module
    configuration=module.ClientConfig(base_url='https://uncontacted.invalid/v1',model='fake-model',key_env_name='P5A_FAKE_KEY_DO_NOT_READ')
    loop=asyncio.new_event_loop()  # asyncio's own wakeup socket predates the no-network assertion.
    def forbidden(*args,**kwargs): raise AssertionError('network or key access before lock')
    monkeypatch.setattr(socket,'socket',forbidden)
    monkeypatch.setattr(module,'read_key',forbidden)
    client=module.CompatibleClient(configuration)
    try:
        with pytest.raises(RuntimeError,match='P5a|disabled|locked'):
            loop.run_until_complete(client.complete([],[],max_completion_tokens=4))
    finally: loop.close()


def test_dry_run_never_reads_key_or_opens_socket(monkeypatch):
    from qi_harness import client as module
    configuration=module.ClientConfig(base_url='https://uncontacted.invalid/v1',model='fake-model',
                                      key_env_name='P5A_FAKE_KEY_DO_NOT_READ',dry_run=True)
    loop=asyncio.new_event_loop()
    def forbidden(*args,**kwargs): raise AssertionError('dry-run opened network or read key')
    monkeypatch.setattr(socket,'socket',forbidden)
    monkeypatch.setattr(module,'read_key',forbidden)
    try: reply=loop.run_until_complete(module.CompatibleClient(configuration).complete([],[],max_completion_tokens=4))
    finally: loop.close()
    assert reply.input_tokens==reply.output_tokens==0


def test_loopback_opt_in_rejects_nonloopback_url():
    from qi_harness.client import ClientConfig,CompatibleClient
    with pytest.raises(ValueError):
        CompatibleClient(ClientConfig(base_url='https://uncontacted.invalid/v1',model='fake',
                                     key_env_name='P5A_FAKE_KEY',allow_loopback_test=True))


def test_missing_price_refuses_before_loopback_socket_or_key_lookup(monkeypatch,tmp_path):
    from qi_harness import client as module
    from qi_harness.budget import PriceBook,BudgetController
    prereg=tmp_path/'fake_prereg.yaml'
    prereg.write_text('budgets:\n  api_usd_cap: 100\n  gpu_usd_cap: 100\n  total_usd_cap: 150\n  stop_and_report_at_fraction: 0.8\n')
    budget=BudgetController(PriceBook({}),prereg_path=prereg,spend_path=tmp_path/'spend.csv')
    configuration=module.ClientConfig(base_url='http://127.0.0.1:1/v1',model='unpriced',
                                      key_env_name='P5A_FAKE_UNREAD_KEY',allow_loopback_test=True)
    loop=asyncio.new_event_loop()
    def forbidden(*args,**kwargs): raise AssertionError('unpriced call touched key/network')
    monkeypatch.setattr(module,'read_key',forbidden)
    monkeypatch.setattr(socket,'socket',forbidden)
    try:
        with pytest.raises(ValueError):
            loop.run_until_complete(module.CompatibleClient(configuration,budget=budget).complete([],[],max_completion_tokens=4))
    finally: loop.close()


def test_actual_compatible_wire_path_against_local_fake_http_shim(monkeypatch,tmp_path):
    """Only a loopback server and a deliberately planted fake key are allowed."""
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    import threading
    from qi_harness.client import ClientConfig,CompatibleClient
    from qi_harness.budget import PriceBook,BudgetController
    received=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            received.append((self.path,body,self.headers.get('Authorization')))
            payload={'choices':[{'message':{'role':'assistant','content':'fixture',
                      'tool_calls':[{'id':'call1','type':'function','function':{
                          'name':'list_files','arguments':'{}'}}]}}],
                     'usage':{'prompt_tokens':11,'completion_tokens':5}}
            encoded=json.dumps(payload).encode()
            self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(encoded)));self.end_headers();self.wfile.write(encoded)
        def log_message(self,*args): pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    fake='P5A_FAKE_VALUE_NOT_A_CREDENTIAL_123'
    monkeypatch.setenv('P5A_FAKE_TEST_KEY',fake)
    prereg=tmp_path/'fake_prereg.yaml'
    prereg.write_text('budgets:\n  api_usd_cap: 100\n  gpu_usd_cap: 100\n  total_usd_cap: 150\n  stop_and_report_at_fraction: 0.8\n')
    budget=BudgetController(PriceBook({'fake-priced-model':{'input_per_million':'1','output_per_million':'2'}}),
                            prereg_path=prereg,spend_path=tmp_path/'spend.csv')
    try:
        client=CompatibleClient(ClientConfig(base_url=f'http://127.0.0.1:{server.server_port}/v1',
                                model='fake-priced-model',key_env_name='P5A_FAKE_TEST_KEY',allow_loopback_test=True),budget=budget)
        reply=asyncio.run(client.complete([{'role':'user','content':'fixture'}],[],max_completion_tokens=17))
        assert (reply.input_tokens,reply.output_tokens)==(11,5)
        assert reply.tool_calls[0].name=='list_files' and reply.tool_calls[0].arguments=={}
        path,body,authorization=received[0]
        assert path=='/v1/chat/completions' and body['model']=='fake-priced-model'
        assert body.get('max_tokens')==17 or body.get('max_completion_tokens')==17
        assert authorization=='Bearer '+fake
        assert fake not in repr(reply)
        assert fake not in (tmp_path/'spend.csv').read_text()
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)
