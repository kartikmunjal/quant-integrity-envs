"""P5a pilot planning only: provider execution remains unconditionally locked."""
import argparse
import json
from qi_harness.client import read_key  # call-time helper; never invoked while P5a is locked

DEFAULT_WINDOWS={'E1':[1002500,1002599],'E2':[1000800,1000899],'E5':[1005500,1005599],'E6':[1003500,1003599]}


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',required=True)
    parser.add_argument('--episodes-per-cell',type=int,default=2)
    parser.add_argument('--dev-seed-window',help='JSON object mapping environment to inclusive [first,last]')
    parser.add_argument('--concurrency',type=int,default=1)
    parser.add_argument('--key-env-name',default='OPENAI_API_KEY')
    parser.add_argument('--confirm-spend',action='store_true')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args(argv)
    if args.episodes_per_cell<1 or args.concurrency<1:raise ValueError('positive pilot counts required')
    windows=json.loads(args.dev_seed_window) if args.dev_seed_window else DEFAULT_WINDOWS
    if set(windows)!=set(DEFAULT_WINDOWS):raise ValueError('all four supported environment windows required')
    for first,last in windows.values():
        if type(first) is not int or type(last) is not int or not 1000000<=first<=last<=1009999:
            raise ValueError('dev seeds only')
        if last-first+1<args.episodes_per_cell:raise ValueError('window too small')
    plan={'model':args.model,'episodes_per_cell':args.episodes_per_cell,'dev_seed_windows':windows,'concurrency':args.concurrency,
          'key_env_name':args.key_env_name,'provider_execution_locked':True,'dry_run':args.dry_run,
          'note':'no key lookup, socket, evaluation or spend; owner authorization and measured prices required in a later phase'}
    if args.dry_run:return plan
    raise RuntimeError('P5a pilot execution locked, including --confirm-spend; no credential lookup performed')


if __name__=='__main__':
    value=main()
    if value is not None:print(json.dumps(value,sort_keys=True,indent=2))
