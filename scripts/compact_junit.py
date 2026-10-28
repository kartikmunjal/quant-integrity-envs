"""Preserve original JUnit bytes locally; bound oversized display IDs/text."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def compact(path,archive_dir):
    path=Path(path);archive_dir=Path(archive_dir)
    raw=path.read_bytes()
    if len(raw)<=512*1024:return None
    identity=hashlib.sha256(raw).hexdigest()
    archive_dir.mkdir(parents=True,exist_ok=True)
    destination=archive_dir/(path.name+'-'+identity[:16]+'.gz')
    packed=gzip.compress(raw,mtime=0)
    if destination.exists() and destination.read_bytes()!=packed:raise ValueError('archive collision')
    destination.write_bytes(packed)
    tree=ET.fromstring(raw)
    for node in tree.iter():
        for key,value in list(node.attrib.items()):
            if len(value)>200:node.set(key,value[:160]+' [sha256:'+hashlib.sha256(value.encode()).hexdigest()+']')
        if node.text and len(node.text)>4000:node.text=node.text[:4000]+'\n[full bytes retained in hashed local XML archive]'
    short=ET.tostring(tree,encoding='utf-8',xml_declaration=True)+b'\n'
    if len(short)>512*1024:raise ValueError('bounded JUnit summary still oversized; original retained')
    path.write_bytes(short)
    return {'original_path':str(path),'original_bytes':len(raw),'original_sha256':identity,
            'path':str(destination),'bytes':len(packed),'sha256':hashlib.sha256(packed).hexdigest(),
            'summary_bytes':len(short),'summary_sha256':hashlib.sha256(short).hexdigest()}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('path');parser.add_argument('--archive-dir',required=True)
    args=parser.parse_args();print(json.dumps(compact(args.path,args.archive_dir)))
