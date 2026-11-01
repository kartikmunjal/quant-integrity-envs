"""Independent fake-price accounting tests; no model calls or real spend."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import pytest


def controller(tmp_path):
    from qi_harness.budget import BudgetController,PriceBook
    prereg=tmp_path/'fake_prereg.yaml'
    prereg.write_text('budgets:\n  api_usd_cap: 100\n  gpu_usd_cap: 100\n  total_usd_cap: 150\n  stop_and_report_at_fraction: 0.8\n')
    book=PriceBook({'fake':{'input_per_million':'1000000','output_per_million':'1000000'}})
    spend=tmp_path/'spend.csv'
    return BudgetController(book,prereg_path=prereg,spend_path=spend),spend


def test_price_book_exact_decimal_and_missing_model_refusal():
    from qi_harness.budget import PriceBook
    book=PriceBook({'fake':{'input_per_million':'0.15','output_per_million':'0.60'}})
    assert book.cost('fake',1000000,500000)==Decimal('.45')
    with pytest.raises(ValueError): book.cost('missing',1,1)
    for input_tokens,output_tokens in ((-1,0),(0,-1),(True,1),(1.5,1)):
        with pytest.raises(ValueError): book.cost('fake',input_tokens,output_tokens)


def test_committed_price_template_has_no_unmeasured_prices():
    import json
    path=Path(__file__).resolve().parents[2]/'configs/model_prices.json'
    assert json.loads(path.read_text())['models']=={}


def test_empty_price_table_refuses_before_actual_spend(tmp_path):
    from qi_harness.budget import PriceBook,BudgetController
    prereg=tmp_path/'prereg.yaml'
    prereg.write_text('budgets:\n  api_usd_cap: 100\n  gpu_usd_cap: 100\n  total_usd_cap: 150\n  stop_and_report_at_fraction: 0.8\n')
    spend=tmp_path/'spend.csv'
    instance=BudgetController(PriceBook({}),prereg_path=prereg,spend_path=spend)
    with pytest.raises(ValueError): instance.reserve('unpriced',10,10)
    assert not spend.exists()


@pytest.mark.parametrize('amount',[80,100,101])
def test_reservation_stops_at_eighty_and_refuses_cap_before_delegate(tmp_path,amount):
    instance,spend=controller(tmp_path)
    with pytest.raises(RuntimeError): instance.reserve('fake',amount,0)
    assert not spend.exists()  # estimated reservations are never metered spend


def test_inflight_reservations_are_locked_and_cannot_double_authorize(tmp_path):
    instance,spend=controller(tmp_path)
    def reserve():
        try: return instance.reserve('fake',50,0)
        except RuntimeError: return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda unused:reserve(),range(2)))
    assert sum(item is not None for item in results)==1
    assert not spend.exists()
    instance.cancel(next(item for item in results if item is not None))
    assert instance.reserve('fake',50,0) is not None


def test_separate_controllers_share_inflight_authorization_for_same_ledger(tmp_path):
    from qi_harness.budget import BudgetController,PriceBook
    first,spend=controller(tmp_path)
    second=BudgetController(PriceBook({'fake':{'input_per_million':'1000000','output_per_million':'1000000'}}),
                            prereg_path=tmp_path/'fake_prereg.yaml',spend_path=spend)
    reservation=first.reserve('fake',50,0)
    try:
        with pytest.raises(RuntimeError): second.reserve('fake',50,0)
        assert not spend.exists()
    finally: first.cancel(reservation)


def test_actual_usage_settlement_and_stop_eighty_are_recorded_honestly(tmp_path):
    from scripts.budget_gate import read_spend
    instance,spend=controller(tmp_path)
    reservation=instance.reserve('fake',70,0)
    assert not spend.exists()
    decision=instance.settle(reservation,80,0)
    assert decision.stop_required
    assert read_spend(spend)['api']==Decimal('80')
    assert ',stop' in spend.read_text()
    with pytest.raises(RuntimeError): instance.reserve('fake',1,0)


def test_actual_overrun_never_disappears_as_refused_or_unaccounted_spend(tmp_path):
    from scripts.budget_gate import read_spend
    instance,spend=controller(tmp_path)
    reservation=instance.reserve('fake',10,0)
    decision=instance.settle(reservation,110,0)
    assert decision.stop_required
    assert read_spend(spend)['api']==Decimal('110')
    assert 'refused' not in spend.read_text()
    with pytest.raises(RuntimeError): instance.reserve('fake',1,0)


def test_repeated_settlement_cannot_duplicate_metered_cost(tmp_path):
    from scripts.budget_gate import read_spend
    instance,spend=controller(tmp_path)
    reservation=instance.reserve('fake',10,0)
    instance.settle(reservation,8,0)
    with pytest.raises(ValueError): instance.settle(reservation,8,0)
    assert read_spend(spend)['api']==Decimal('8')


def test_uncertain_dispatch_retains_reservation_and_forbids_silent_cancellation(tmp_path):
    import json
    instance,spend=controller(tmp_path)
    reservation=instance.reserve('fake',1,0)
    instance.uncertain(reservation)
    assert not spend.exists()  # unknown usage is not an invented actual charge
    state=json.loads(instance.reservations_path.read_text())
    assert state['stop'] and state['pending'][reservation]['uncertain']
    with pytest.raises(RuntimeError): instance.cancel(reservation)
    with pytest.raises(RuntimeError): instance.reserve('fake',1,0)
