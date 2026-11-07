import pytest

from agentops import Handoff, InvalidHandoff

OK = dict(
    outcome="Add lint gate to deploy path",
    shipped="branch feat/lint-gate, 3 files",
    verified="pytest: 27 passed, 0 failed",
    did_not_do="No prod deploy (disabled by design)",
    needs_human="nothing",
    next_step="Wire the gate into CI",
)


def test_valid_handoff_renders_all_six_fields():
    out = Handoff(**OK).render()
    assert out.splitlines()[0] == "HANDOFF"
    assert len(out.splitlines()) == 7


def test_verified_without_a_number_is_rejected():
    with pytest.raises(InvalidHandoff, match="number"):
        Handoff(**{**OK, "verified": "looks good to me"}).render()


def test_empty_field_is_rejected():
    with pytest.raises(InvalidHandoff, match="empty"):
        Handoff(**{**OK, "shipped": "  "}).render()


def test_multiline_and_overlong_fields_are_rejected():
    with pytest.raises(InvalidHandoff, match="one line"):
        Handoff(**{**OK, "outcome": "a\nb"}).render()
    with pytest.raises(InvalidHandoff, match="limit"):
        Handoff(**{**OK, "outcome": "x" * 161}).render()
