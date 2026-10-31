#!/usr/bin/env python3
"""One-regex release scan of text files, paths, refs, messages and streamed diffs.

Output contains only status, total occurrences and redacted locations/term indices.
Term indices are physical 1-based lines in the supplied file, including skipped
blank lines. Working files are tracked or untracked and not ignored; binary
and symlink content is not scanned.
"""
from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass,field
import os
from pathlib import Path
import re
import subprocess
import sys
import threading

HIT_LIMIT=200


class Matcher:
    """One compiled literal union; short-token boundaries are checked per match.

    A lookahead includes overlaps. Prefix aliases retain all terms starting at
    the same offset, rather than letting a longer alternative conceal a prefix.
    Redaction uses the same union without token boundaries: even a short term
    embedded in a reported pathname or hash must not be exposed in output.
    """
    def __init__(self,terms):
        if not terms:raise ValueError('empty terms')
        self.terms=dict(terms)
        ordered=sorted(terms,key=lambda item:(-len(item[1]),item[0]))
        self.regex=re.compile('(?=(?:'+'|'.join(f'(?P<t{i}>{re.escape(term)})' for i,term in ordered)+'))',re.IGNORECASE)
        folded={}
        for i,term in terms:folded.setdefault(term.casefold(),[]).append((i,term))
        self.prefixes={}
        for i,term in terms:
            key=term.casefold()
            self.prefixes[i]=[item for end in range(1,len(key)+1) for item in folded.get(key[:end],[])]

    def _matches(self,text,boundaries):
        for match in self.regex.finditer(text):
            primary=int(match.lastgroup[1:]);start=match.start()
            for index,term in self.prefixes[primary]:
                end=start+len(term)
                if index==primary:end=match.end(match.lastgroup)
                elif text[start:end].casefold()!=term.casefold():continue
                if boundaries and len(term)<=5:
                    if start and text[start-1].isalnum():continue
                    if end<len(text) and text[end].isalnum():continue
                yield index,start,end

    def matches(self,text):return self._matches(text,True)

    def redact(self,text):
        spans=sorted((a,b,index) for index,a,b in self._matches(text,False))
        merged=[]
        for start,end,index in spans:
            if merged and start<=merged[-1][1]:
                old=merged[-1];merged[-1]=(old[0],max(old[1],end),min(old[2],index))
            else:merged.append((start,end,index))
        parts=[];cursor=0
        for start,end,index in merged:
            parts.extend((text[cursor:start],f'[{index}]'));cursor=end
        parts.append(text[cursor:])
        # A path may contain newlines/control characters. Keep every hit one line.
        return ''.join(c if c.isprintable() else c.encode('unicode_escape').decode('ascii') for c in ''.join(parts))


@dataclass
class Result:
    total:int=0
    hits:list[str]=field(default_factory=list)
    term_hits:Counter=field(default_factory=Counter)

    def add(self,location,text,matcher):
        for index,_,_ in matcher.matches(text):
            self.total+=1
            self.term_hits[index]+=1
            if len(self.hits)<HIT_LIMIT:
                self.hits.append(f'{matcher.redact(location)} term={index}')

    def absorb(self,other):
        self.total+=other.total
        self.term_hits.update(other.term_hits)
        self.hits.extend(other.hits[:HIT_LIMIT-len(self.hits)])


class Progress:
    def __init__(self,interval=60):
        self.interval=interval;self.commits=0;self.stop=threading.Event()

    def __enter__(self):
        def heartbeat():
            while not self.stop.wait(self.interval):
                print(f'commits scanned: {self.commits}',file=sys.stderr,flush=True)
        self.thread=threading.Thread(target=heartbeat,daemon=True);self.thread.start();return self

    def __exit__(self,*args):
        self.stop.set();self.thread.join()


def _terms(path):
    result=[]
    with path.open('r',encoding='utf-8',newline='') as stream:
        for index,line in enumerate(stream,1):
            term=line.rstrip('\n').rstrip('\r')
            if term.strip():result.append((index,term))
    if not result:raise ValueError('empty terms')
    return result


def _git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL)


def _working_tree(repo,matcher,result):
    names=set(_git(repo,'ls-files','--cached','-z').split(b'\0'))
    names.update(_git(repo,'ls-files','--others','--exclude-standard','-z').split(b'\0'))
    for raw in sorted(names):
        if not raw:continue
        relative=os.fsdecode(raw);path=repo/relative
        # Never follow a symlink in any component, including a replaced tracked
        # directory. Deleted tracked paths have no working-tree content.
        if any(parent.is_symlink() for parent in (path,*path.parents) if parent!=repo):continue
        if not path.is_file():continue
        pending=Result()
        # A late NUL/decoding error discards all hits and term counts in a file.
        try:
            with path.open('r',encoding='utf-8',errors='strict') as stream:
                for number,line in enumerate(stream,1):
                    if '\0' in line:break
                    pending.add(f'working/{relative}:{number}',line,matcher)
                else:result.absorb(pending)
        except UnicodeError:continue


def _path(raw):
    raw=raw.rstrip(b'\n')
    if raw.startswith(b'"'):
        raw=ast.literal_eval('b'+raw.decode('ascii'))
    return os.fsdecode(raw)


def _diff_path(raw):
    """Decode identical a/b names (--no-renames), including Git C quoting."""
    raw=raw.rstrip(b'\n')
    if raw.startswith(b'"'):
        cursor=1
        while cursor<len(raw):
            if raw[cursor:cursor+1]==b'\\':cursor+=2;continue
            if raw[cursor:cursor+1]==b'"':break
            cursor+=1
        left=raw[:cursor+1];right=raw[cursor+2:]
    else:
        n=(len(raw)-5)//2
        left=raw[:n+2];right=raw[n+3:]
    old=_path(left);new=_path(right)
    if not old.startswith('a/') or not new.startswith('b/') or old[2:]!=new[2:]:
        raise ValueError('unexpected diff paths')
    return old[2:]


class History:
    def __init__(self,matcher,result,progress):
        self.matcher=matcher;self.result=result;self.progress=progress
        self.commit='';self.file='';self.message=False;self.message_line=0
        self.seen=set();self.new_message=False;self.hunk=False

    def feed(self,raw):
        if self.message:
            self._message(raw);return
        if raw.startswith(b'\x1e'):
            commit,body=raw[1:].split(b'\0',1)
            if len(commit)!=40 or any(c not in b'0123456789abcdef' for c in commit):raise ValueError('commit framing')
            self.commit=commit.decode('ascii')[:12];self.file='';self.hunk=False
            self.new_message=commit not in self.seen;self.seen.add(commit)
            self.progress.commits=len(self.seen);self.message_line=0;self.message=True
            self._message(body);return
        if raw.startswith(b'diff --git '):
            self.file=_diff_path(raw[len(b'diff --git '):]);self.hunk=False
            self.result.add(self.location(1,'path'),self.file,self.matcher);return
        if not self.file:return  # Git's empty record separators, not diff content.
        if raw.startswith(b'@@ '):
            fields=raw.split(b'@@',2)[1].split()
            old=fields[0][1:].split(b',');new=fields[1][1:].split(b',')
            self.old=int(old[0]);self.new=int(new[0])
            self.old_left=int(old[1]) if len(old)>1 else 1
            self.new_left=int(new[1]) if len(new)>1 else 1
            self.hunk=True
            self.result.add(self.location(max(1,self.new),'hunk'),raw.decode('utf-8',errors='replace'),self.matcher);return
        if self.hunk and raw[:1] in (b'+',b'-',b' '):
            mark=raw[:1]
            if mark==b'-':number=self.old;side='old';self.old+=1;self.old_left-=1
            elif mark==b'+':number=self.new;side='new';self.new+=1;self.new_left-=1
            else:
                number=self.new;side='context';self.old+=1;self.new+=1;self.old_left-=1;self.new_left-=1
            self.result.add(self.location(number,side),raw[1:].decode('utf-8',errors='replace'),self.matcher)
            if self.old_left==self.new_left==0:self.hunk=False
            return
        # File headers repeat the already-decoded path. Binary patch contents
        # are not emitted by git log; its ordinary binary marker is metadata.
        if raw.startswith((b'--- ',b'+++ ')):return
        self.result.add(self.location(1,'metadata'),raw.decode('utf-8',errors='replace'),self.matcher)

    def location(self,number,side):return f'history/{self.commit}/{self.file}:{number} ({side})'

    def _message(self,raw):
        body,separator,_=raw.partition(b'\0')
        if body:
            for line in body.decode('utf-8',errors='replace').splitlines():
                self.message_line+=1
                if self.new_message:self.result.add(f'commit/{self.commit}:{self.message_line}',line,self.matcher)
        if separator:self.message=False


def scan(repo:Path,terms_path:Path)->Result:
    matcher=Matcher(_terms(terms_path));result=Result()
    with Progress() as progress:
        _working_tree(repo,matcher,result)
        for raw in _git(repo,'ls-files','--cached','-z').split(b'\0'):
            if raw:
                name=os.fsdecode(raw);result.add(f'tracked-path/{name}:1',name,matcher)
        refs=_git(repo,'for-each-ref','--format=%(refname)','refs/heads','refs/remotes','refs/tags')
        for raw in refs.splitlines():
            ref=os.fsdecode(raw)
            kind='tag' if ref.startswith('refs/tags/') else 'branch'
            name=ref.split('/',2)[2];result.add(f'{kind}/{name}:1',name,matcher)
        args=['git','-C',str(repo),'-c','core.quotePath=true','log','--all','-p','--root','-m',
              '--no-renames','--no-color','--no-ext-diff','--no-textconv','--format=%x1e%H%x00%B%x00','--']
        history=History(matcher,result,progress)
        with subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL) as process:
            try:
                for raw in process.stdout:history.feed(raw)
            except BaseException:
                process.terminate();process.wait();raise
            if process.wait()!=0:raise ValueError('history scan failed')
        if history.message:raise ValueError('incomplete history framing')
    return result


def main()->int:
    path=os.environ.get('RELEASE_REVIEW_TERMS')
    try:
        if not path:raise ValueError('terms unset')
        result=scan(Path.cwd(),Path(path))
    except (OSError,ValueError,SyntaxError,re.error,subprocess.SubprocessError):
        print('FAIL\nTOTAL 0');return 2
    print('FAIL' if result.total else 'PASS')
    print(f'TOTAL {result.total}')
    for index,count in sorted(result.term_hits.items(),key=lambda item:(-item[1],item[0]))[:20]:
        print(f'SUMMARY term={index} hits={count}')
    for hit in result.hits:print(hit)
    return 1 if result.total else 0


if __name__=='__main__':raise SystemExit(main())
