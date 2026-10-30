"""Release scanner validation uses synthetic terms and disposable repositories only."""
import os
import subprocess
from pathlib import Path
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/release_review.py'


def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL)


@pytest.fixture
def repo(tmp_path):
    path=tmp_path/'repo';path.mkdir()
    git(path,'init','-q');git(path,'config','user.email','test@example.invalid');git(path,'config','user.name','Test')
    (path/'safe.txt').write_text('public material\n');git(path,'add','.');git(path,'commit','-qm','initial')
    return path


def run_review(repo,terms):
    env=dict(os.environ)
    if terms is None:env.pop('RELEASE_REVIEW_TERMS',None)
    else:env['RELEASE_REVIEW_TERMS']=str(terms)
    return subprocess.run([os.sys.executable,str(SCRIPT)],cwd=repo,env=env,text=True,capture_output=True)


def terms_file(repo,text):
    path=repo.parent/'fake_terms.txt';path.write_bytes(text.encode());return path


def test_clean_pass(repo):
    r=run_review(repo,terms_file(repo,'zzfakesecret\n'))
    assert r.returncode==0 and r.stdout=='PASS\nTOTAL 0\n'


@pytest.mark.parametrize('text,hit',[
    ('prefixZZFAKESECRETsuffix',True),
    ('abc',True),('ABC',True),('xabcx',False),('00abcf09',False),
    ('x_abc-y',True),('x.abc/y',True),('éabcé',False)])
def test_long_substring_short_boundaries_and_hex(repo,text,hit):
    (repo/'draft.txt').write_text(text+'\n')
    r=run_review(repo,terms_file(repo,'zzfakesecret\nabc\n'))
    assert r.returncode==(1 if hit else 0)
    assert 'zzfakesecret' not in (r.stdout+r.stderr).lower()
    assert 'abc' not in (r.stdout+r.stderr).lower()
    if hit:assert 'working/draft.txt:1 term=' in r.stdout


def test_path_message_branch_and_tag_hits_are_redacted(repo):
    secret='zzfakesecret';p=repo/(secret+'.txt');p.write_text('ordinary\n')
    git(repo,'add','.');git(repo,'commit','-qm','message '+secret)
    git(repo,'tag',secret+'-tag');git(repo,'branch',secret+'-branch')
    r=run_review(repo,terms_file(repo,secret+'\n'))
    assert r.returncode==1
    for label in ('tracked-path/','commit/','tag/','branch/'):
        assert label in r.stdout
    assert secret not in r.stdout+r.stderr
    assert 'message ' not in r.stdout+r.stderr


def test_deleted_line_uses_old_hunk_line_number(repo):
    secret='zzfakesecret';p=repo/'old.txt';p.write_text('first\n'+secret+' hidden sentence\nlast\n')
    git(repo,'add','.');git(repo,'commit','-qm','add file')
    p.write_text('first\nlast\n');git(repo,'add','.');git(repo,'commit','-qm','remove line')
    deletion=git(repo,'rev-parse','--short=12','HEAD').decode().strip()
    r=run_review(repo,terms_file(repo,secret+'\n'))
    assert r.returncode==1
    assert f'history/{deletion}/old.txt:2 (old) term=1' in r.stdout
    assert secret not in r.stdout+r.stderr and 'hidden sentence' not in r.stdout+r.stderr


def test_worktree_ignored_text_included_binary_and_git_excluded(repo):
    secret='zzfakesecret';(repo/'.gitignore').write_text('ignored.txt\n')
    (repo/'ignored.txt').write_text(secret+'\n')
    (repo/'binary.bin').write_bytes(secret.encode()+b'\x00later')
    (repo/'.git'/'not_source').write_text(secret+'\n')
    r=run_review(repo,terms_file(repo,secret+'\n'))
    assert r.returncode==1 and 'ignored.txt:1' in r.stdout
    assert 'binary.bin' not in r.stdout and 'not_source' not in r.stdout


def test_blank_lines_cr_and_physical_term_indices(repo):
    (repo/'draft.txt').write_text('ZZFAKESECRET abc\n')
    r=run_review(repo,terms_file(repo,'\r\nzzfakesecret\r\n \r\nabc\r\n'))
    assert r.returncode==1 and 'term=2' in r.stdout and 'term=4' in r.stdout
    assert '\r' not in r.stdout


@pytest.mark.parametrize('kind',['unset','missing','empty'])
def test_error_exit_codes_without_sensitive_error_output(repo,kind):
    terms=None if kind=='unset' else repo.parent/'missing-fake.txt' if kind=='missing' else terms_file(repo,'\n \r\n')
    r=run_review(repo,terms)
    assert r.returncode==2 and r.stdout=='FAIL\nTOTAL 0\n'
    assert r.stderr==''


def test_hit_cap_keeps_total_and_never_prints_line(repo):
    (repo/'many.txt').write_text(('zzfakesecret confidential sentence\n')*250)
    r=run_review(repo,terms_file(repo,'zzfakesecret\n'))
    assert r.returncode==1 and r.stdout.splitlines()[1]=='TOTAL 250'
    assert len(r.stdout.splitlines())==202
    assert 'zzfakesecret' not in r.stdout+r.stderr and 'confidential sentence' not in r.stdout+r.stderr


def test_unicode_and_quoted_history_paths(repo):
    secret='zzfakesecret';name='spaced ü\tname.txt';p=repo/name;p.write_text(secret+'\n')
    git(repo,'add','.');git(repo,'commit','-qm','addition');p.unlink();git(repo,'add','-u');git(repo,'commit','-qm','deletion')
    r=run_review(repo,terms_file(repo,secret+'\n'))
    assert r.returncode==1 and '(old) term=1' in r.stdout
    assert secret not in r.stdout+r.stderr


def test_single_regex_overlap_prefixes_and_single_history_stream(repo,monkeypatch):
    from scripts import release_review as m
    compiled=[];real_compile=m.re.compile
    def compile_once(*args,**kwargs):compiled.append(args[0]);return real_compile(*args,**kwargs)
    monkeypatch.setattr(m.re,'compile',compile_once)
    matcher=m.Matcher([(1,'abcdef'),(2,'abcdefg'),(3,'cdefghi')])
    assert {x[0] for x in matcher.matches('ABCDEFGHI')}=={1,2,3}
    assert len(compiled)==1
    commands=[];real=m.subprocess.Popen
    def popen(args,*a,**k):commands.append(args);return real(args,*a,**k)
    monkeypatch.setattr(m.subprocess,'Popen',popen)
    result=m.scan(repo,terms_file(repo,'zzfakesecret\n'))
    assert result.total==0
    logs=[cmd for cmd in commands if 'log' in cmd]
    assert len(logs)==1 and '--all' in logs[0] and '-p' in logs[0]


def test_progress_heartbeat(capsys):
    from scripts.release_review import Progress
    import time
    with Progress(interval=.01) as progress:
        progress.commits=17;time.sleep(.04)
    assert 'commits scanned: 17' in capsys.readouterr().err


def test_all_refs_include_commits_outside_current_branch(repo):
    secret='zzfakesecret';branch=git(repo,'symbolic-ref','--short','HEAD').decode().strip()
    git(repo,'checkout','-qb','side')
    (repo/'side.txt').write_text(secret+'\n');git(repo,'add','.');git(repo,'commit','-qm','side commit')
    git(repo,'checkout','-q',branch)
    r=run_review(repo,terms_file(repo,secret+'\n'))
    assert r.returncode==1 and '/side.txt:1 (new)' in r.stdout
    assert secret not in r.stdout+r.stderr


def test_path_redaction_also_hides_nonmatching_short_substrings(repo):
    (repo/'xabcx.txt').write_text('zzfakesecret\n')
    r=run_review(repo,terms_file(repo,'zzfakesecret\nabc\n'))
    assert r.returncode==1 and 'TOTAL 1' in r.stdout
    assert 'abc' not in r.stdout+r.stderr and 'zzfakesecret' not in r.stdout+r.stderr


def test_binary_late_nul_and_external_symlink_are_not_read(repo):
    (repo/'late.bin').write_bytes(b'zzfakesecret\nnext\n\x00end')
    external=repo.parent/'fake_external.txt';external.write_text('zzfakesecret\n')
    (repo/'link.txt').symlink_to(external)
    r=run_review(repo,terms_file(repo,'zzfakesecret\n'))
    assert r.returncode==0 and r.stdout=='PASS\nTOTAL 0\n'


def benchmark_history(root,count=2000):
    """Build a synthetic history in one fast-import; time only the scanner CLI."""
    import time
    repo=root/'history';repo.mkdir();git(repo,'init','-q')
    stream=[]
    for n in range(count):
        message=f'synthetic commit {n}\n'.encode();body=f'public iteration {n}\n'.encode()
        stream.append(f'commit refs/heads/main\ncommitter Synthetic <test@example.invalid> {1700000000+n} +0000\ndata {len(message)}\n'.encode()+message+b'M 100644 inline payload.txt\n'+f'data {len(body)}\n'.encode()+body+b'\n')
    subprocess.run(['git','-C',str(repo),'fast-import','--quiet'],input=b''.join(stream),check=True,capture_output=True)
    git(repo,'symbolic-ref','HEAD','refs/heads/main');git(repo,'reset','--hard','-q')
    actual=int(git(repo,'rev-list','--all','--count'))
    terms=terms_file(repo,''.join(f'zzsyntheticneedle{n:03d}\n' for n in range(100)))
    started=time.monotonic();r=run_review(repo,terms);elapsed=time.monotonic()-started
    return {'commits':actual,'fake_terms':100,'scanner_wall_seconds':elapsed,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}


def test_two_thousand_commit_history_finishes_quickly(tmp_path):
    result=benchmark_history(tmp_path)
    assert result['commits']==2000 and result['exit_code']==0
    assert result['stdout']=='PASS\nTOTAL 0\n' and result['stderr']==''
    assert result['scanner_wall_seconds']<60
