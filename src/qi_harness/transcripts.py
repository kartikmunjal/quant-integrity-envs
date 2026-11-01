"""Bounded canonical transcripts with redaction before hashing or persistence."""
import hashlib
import json
from pathlib import Path


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def write_transcript(path,record,secrets=(),max_bytes=2097152):
    if type(max_bytes) is not int or max_bytes<256:raise ValueError('transcript cap must be at least256 bytes')
    def redact(value):
        if isinstance(value,str):
            for secret in secrets:
                if secret:value=value.replace(secret,'[REDACTED]')
            return value
        if isinstance(value,dict):return {redact(k):redact(v) for k,v in value.items() if str(k).lower() not in ('authorization','api_key','key_value')}
        if isinstance(value,(list,tuple)):return [redact(v) for v in value]
        return value
    clean=redact(record);raw=canonical(clean)+b'\n';original=raw;truncated=len(raw)>max_bytes
    if truncated:
        # Retain outcome metadata and a digest of the complete sanitized record.
        summary={key:clean[key] for key in ('environment','seed','tier','reward','reason','turns','input_tokens','output_tokens','total_tokens','wall_seconds','hack_monitors') if key in clean}
        summary.update(truncated=True,original_sha256=hashlib.sha256(original).hexdigest(),original_bytes=len(original),message_count=len(clean.get('messages',[])))
        preview=original[:max_bytes].decode(errors='replace')
        while True:
            candidate={**summary,'preview':preview};raw=canonical(candidate)+b'\n'
            if len(raw)<=max_bytes:break
            if not preview:
                summary={key:summary[key] for key in ('truncated','original_sha256','original_bytes')};raw=canonical(summary)+b'\n';break
            preview=preview[:max(0,len(preview)//2)]
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as output:output.write(raw)
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'truncated':truncated,
            'original_sanitized_sha256':hashlib.sha256(original).hexdigest(),'original_sanitized_bytes':len(original)}


def read_transcript(path,expected_sha256):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError('transcript hash mismatch')
    return json.loads(raw)
