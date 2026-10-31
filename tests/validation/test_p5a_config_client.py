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


def test_actual_compatible_wire_path_against_local_fake_http_shim(monkeypatch):
    """Only a loopback server and a deliberately planted fake key are allowed."""
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    import threading
    from qi_harness.client import ClientConfig,CompatibleClient
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
    try:
        client=CompatibleClient(ClientConfig(base_url=f'http://127.0.0.1:{server.server_port}/v1',
                                model='fake-priced-model',key_env_name='P5A_FAKE_TEST_KEY',allow_loopback_test=True))
        reply=asyncio.run(client.complete([{'role':'user','content':'fixture'}],[],max_completion_tokens=17))
        assert (reply.input_tokens,reply.output_tokens)==(11,5)
        assert reply.tool_calls[0].name=='list_files' and reply.tool_calls[0].arguments=={}
        path,body,authorization=received[0]
        assert path=='/v1/chat/completions' and body['model']=='fake-priced-model'
        assert body.get('max_tokens')==17 or body.get('max_completion_tokens')==17
        assert authorization=='Bearer '+fake
        assert fake not in repr(reply)
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)
