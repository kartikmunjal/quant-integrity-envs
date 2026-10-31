"""Dev-only append-only prompt manifest checks."""
import hashlib
import json
from pathlib import Path


def verify_prompt_manifest(root,manifest_path=None):
    root=Path(root).resolve();path=Path(manifest_path) if manifest_path is not None else root/'results/prompt_manifest.json'
    manifest=json.loads(path.read_text());entries=manifest['entries']
    if not entries:raise ValueError('empty prompt history')
    for index,entry in enumerate(entries,1):
        if entry['version']!=index or entry['seed_partition']!='dev':raise ValueError('prompt versions must be sequential dev-only entries')
        for name,digest in entry['files'].items():
            relative=Path(name)
            if relative.is_absolute() or '..' in relative.parts:raise ValueError('prompt path outside repository')
            resolved=(root/relative).resolve()
            if not resolved.is_relative_to(root):raise ValueError('prompt symlink outside repository')
            if index==len(entries) and hashlib.sha256(resolved.read_bytes()).hexdigest()!=digest:
                raise ValueError('prompt changed without new manifest version')
    return True


def messages_for(environment,task_prompt,root=Path('.')):
    verify_prompt_manifest(root)
    return [{'role':'system','content':(Path(root)/'prompts/tools.md').read_text()+'\n'+(Path(root)/('prompts/'+environment.lower()+'.md')).read_text()},
            {'role':'user','content':task_prompt}]
