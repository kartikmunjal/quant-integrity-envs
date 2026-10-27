"""Public cross-source reconciliation; no oracle input or generator dependency."""
def reconstruct(data,mode='exact'):
    import math
    expected={}
    for listing in data['listings']:
        key=listing['listing_id'];price=listing['anchor_price'];factor=1.;identifier=listing['initial_identifier'];active=True
        records=sorted((a for a in data['audits'] if a['listing_id']==key),key=lambda a:a['day'])
        for audit in records:
            day=audit['day'];split=1.;terminal=None
            for action in data['actions']:
                if action['listing_id']!=key or action['day']!=day:continue
                if action['kind']=='identifier' and mode!='ignore_identifiers':identifier=action['new_identifier']
                if action['kind']=='split' and mode!='ignore_splits':split=action['factor']
                if action['kind']=='delisting' and mode!='ignore_delistings':terminal=action['return']
            factor*=split
            ret=audit['gross_return']-1 if active else 0.
            if terminal is not None:ret=terminal;active=False
            previous=price
            price=price*audit['gross_return']/split if active else 0.
            if mode=='raw_price_returns':ret=price/previous-1 if previous else 0.
            adjusted=price*factor if mode!='reverse_split_adjustment' else price/factor
            expected[key,day]=dict(listing_id=key,day=day,identifier=identifier,ticker=listing['ticker'],active=active,
                price=price,adjusted_price=adjusted,total_return=ret)
    seen=set();flags=[]
    for quote in sorted(data['quotes'],key=lambda q:q['record_id']):
        k=(quote['listing_id'],quote['day']);row=expected.get(k);bad=k in seen or row is None;seen.add(k)
        if row is not None:
            for name in ('identifier','ticker'):
                if quote[name]!=row[name]:bad=True
            for name in ('price','total_return'):
                value=quote[name]
                if type(value) not in (int,float) or not math.isfinite(value) or abs(value-row[name])>1e-8*max(abs(row[name]),1e-12):bad=True
        if bad:flags.append(quote['record_id'])
    rows=[expected[k] for k in sorted(expected)]
    if mode=='ticker_only':
        unique={}
        for row in rows:unique[row['ticker'],row['day']]=row
        rows=list(unique.values())
    if mode=='drop_identifier_history':
        identifiers={a['listing_id']:a['initial_identifier'] for a in data['listings']}
        rows=[r for r in rows if r['identifier']==identifiers[r['listing_id']]]
    if mode=='drop_inactive':rows=[r for r in rows if r['active']]
    if mode=='flag_large_moves':
        flags=[q['record_id'] for q in data['quotes'] if type(q['total_return']) in (int,float) and abs(q['total_return'])>.1]
    if mode=='flag_all':flags=[q['record_id'] for q in data['quotes']]
    if mode=='never_flag':flags=[]
    if mode in ('near_miss','near_small'):
        scale=1.00505 if mode=='near_miss' else 1.002575
        for row in rows:
            row['price']*=scale;row['adjusted_price']*=scale
    if mode=='near_false_flag':flags.append('unknown-but-counted-false-flag')
    return {'universe':rows,'anomalies':sorted(flags)}
