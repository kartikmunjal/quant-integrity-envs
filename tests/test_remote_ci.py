"""Synthetic API fixtures; no network calls or real credentials."""
from scripts import check_remote_ci as ci
import urllib.error


def test_ci_records_real_status_without_saving_token(monkeypatch):
    monkeypatch.setenv('GH_TOKEN','synthetic-test-token')
    sha='a'*40
    def fake(path,token):
        assert token=='synthetic-test-token'
        if path.startswith('/actions/runs?'):
            return {'workflow_runs':[{'id':1,'head_sha':sha,'name':'CI','status':'completed','conclusion':'success','html_url':'fixture'}]}
        return {'jobs':[{'id':2,'name':'test','status':'completed','conclusion':'success','steps':[{'name':'Prepare shared runtime','conclusion':'success'}]}]}
    monkeypatch.setattr(ci,'_get',fake)
    result=ci.check(sha)
    assert result['result']=='pass'
    assert 'synthetic-test-token' not in str(result)


def test_missing_access_is_not_reported_as_ci_failure_or_success(monkeypatch):
    monkeypatch.delenv('GH_TOKEN',raising=False);monkeypatch.delenv('GITHUB_TOKEN',raising=False)
    def unavailable(path,token):raise urllib.error.HTTPError('fixture',404,'not found',{},None)
    monkeypatch.setattr(ci,'_get',unavailable)
    result=ci.check('a'*40)
    assert result['result']=='unavailable' and result['http_code']==404


def test_pending_and_failed_ci_are_distinct(monkeypatch):
    sha='a'*40
    for status,conclusion,expected in [('in_progress',None,'pending'),('completed','failure','fail')]:
        def fake(path,token):
            if path.startswith('/actions/runs?'):return {'workflow_runs':[{'id':1,'head_sha':sha,'name':'CI','status':status,'conclusion':conclusion}]}
            return {'jobs':[{'conclusion':conclusion,'steps':[]}]}
        monkeypatch.setattr(ci,'_get',fake)
        assert ci.check(sha)['result']==expected
