"""Bounded E3 probability submissions executed only in the shared checked runtime."""
from qi_runtime import execute_program
from .reward import parse_submission


async def execute_once(public,source):
    ids=[c['id'] for c in public['candidates']]
    def parse(out):
        try:
            return parse_submission(out,ids)
        except ValueError:
            return None
    return await execute_program(public,source,parse,namespace='e3')
