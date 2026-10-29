"""Prospective round-three freeze approval tests."""
import pytest
from scripts import freeze_p3a3 as freeze


@pytest.mark.parametrize('text',['NOT READY FOR FREEZE','Provisional: no READY FOR FREEZE approval.',''])
def test_negative_or_quoted_review_is_not_approval(text):
    with pytest.raises(ValueError):freeze.require_review_approval(text)


def test_exact_review_approval():
    freeze.require_review_approval('# Review\n\nStatus: READY FOR FREEZE\n')
