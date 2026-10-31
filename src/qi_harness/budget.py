"""Locked reservations plus honest actual-usage accounting using budget_gate rules."""
from contextlib import contextmanager
from decimal import Decimal
import fcntl
import json
import os
from pathlib import Path
import uuid
from scripts.budget_gate import _money,load_limits,read_spend,decide,append_record,GateDecision


class PriceBook:
    def __init__(self,models):
        self.models={}
        for name,row in models.items():
            self.models[name]={key:_money(row[key]) for key in ('input_per_million','output_per_million')}

    def cost(self,model,input_tokens,output_tokens):
        if model not in self.models:raise ValueError('model has no committed price')
        if any(type(v) is not int or v<0 for v in (input_tokens,output_tokens)):
            raise ValueError('usage must be nonnegative integer tokens')
        p=self.models[model]
        return (p['input_per_million']*input_tokens+p['output_per_million']*output_tokens)/Decimal(1_000_000)


class BudgetController:
    def __init__(self,book,prereg_path=Path('prereg.yaml'),spend_path=Path('logs/spend.csv')):
        self.book=book;self.prereg_path=Path(prereg_path);self.spend_path=Path(spend_path)
        self.reservations_path=self.spend_path.with_suffix('.reservations.json')
        self.lock_path=self.spend_path.with_suffix('.lock')

    @contextmanager
    def _locked(self):
        self.lock_path.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(self.lock_path,os.O_CREAT|os.O_RDWR,0o600)
        with os.fdopen(fd,'a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            state=json.loads(self.reservations_path.read_text()) if self.reservations_path.exists() else {'stop':False,'pending':{}}
            try:yield state
            finally:
                temporary=self.reservations_path.with_name(self.reservations_path.name+'.'+uuid.uuid4().hex)
                descriptor=os.open(temporary,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
                with os.fdopen(descriptor,'w') as output:
                    json.dump(state,output,sort_keys=True);output.write('\n');output.flush();os.fsync(output.fileno())
                os.replace(temporary,self.reservations_path)
                fcntl.flock(lock,fcntl.LOCK_UN)

    def reserve(self,model,input_tokens,output_tokens):
        amount=self.book.cost(model,input_tokens,output_tokens)
        with self._locked() as state:
            if state['stop']:raise RuntimeError('budget stop: owner reconciliation required')
            caps,fraction=load_limits(self.prereg_path);totals=read_spend(self.spend_path)
            # Outstanding reservations are commitments, never invented metered spend.
            totals['api']+=sum((Decimal(r['amount']) for r in state['pending'].values()),Decimal(0))
            decision=decide('api',amount,totals,caps,fraction)
            if not decision.accepted or decision.stop_required:
                raise RuntimeError('budget refuses reservation at cap or 80 percent stop threshold')
            identifier=uuid.uuid4().hex
            state['pending'][identifier]={'model':model,'amount':str(amount),'input_limit':input_tokens,'output_limit':output_tokens,'uncertain':False}
            return identifier

    def settle(self,reservation,input_tokens,output_tokens):
        with self._locked() as state:
            if reservation not in state['pending']:raise ValueError('unknown or already settled reservation')
            row=state['pending'][reservation]
            actual=self.book.cost(row['model'],input_tokens,output_tokens)
            caps,fraction=load_limits(self.prereg_path)
            decision=decide('api',actual,read_spend(self.spend_path),caps,fraction)
            overshoot=actual>Decimal(row['amount'])
            stop=decision.stop_required or overshoot or row['uncertain']
            reason=('actual usage exceeded reservation; recorded in full' if overshoot else decision.reason)
            # Payment has happened: even an overrun is recorded, never hidden as refused.
            append_record(self.spend_path,'api',actual,'model token usage '+row['model'],'stop' if stop else 'accepted')
            del state['pending'][reservation]
            state['stop'] |= stop
            return GateDecision(decision.accepted,stop,reason,decision.projected)

    def cancel(self,reservation):
        """Only before dispatch, when it is known no billable request was made."""
        with self._locked() as state:
            if reservation not in state['pending']:raise ValueError('unknown reservation')
            if state['pending'][reservation]['uncertain']:raise RuntimeError('uncertain request cannot be silently cancelled')
            del state['pending'][reservation]

    def uncertain(self,reservation):
        """Retain an unresolved commitment; do not fabricate usage after lost responses."""
        with self._locked() as state:
            if reservation not in state['pending']:raise ValueError('unknown reservation')
            state['pending'][reservation]['uncertain']=True;state['stop']=True
