import json

import pytest

from agentops import Approval, Message, OutboundBlocked, SendGuard

MSG = Message("a@example.test", "Hello", "Draft body")


def make(tmp_path, dry_run=True):
    sent = []
    g = SendGuard(sent.append, dry_run=dry_run, audit_log=tmp_path / "audit.jsonl")
    return g, sent


def test_no_approval_is_blocked(tmp_path):
    g, sent = make(tmp_path, dry_run=False)
    with pytest.raises(OutboundBlocked):
        g.send(MSG)
    assert sent == []


def test_approval_for_a_different_message_is_blocked(tmp_path):
    g, sent = make(tmp_path, dry_run=False)
    other = Message("a@example.test", "Hello", "Draft body, edited")
    with pytest.raises(OutboundBlocked, match="exact message"):
        g.send(MSG, Approval("aaron", other.digest()))
    assert sent == []


def test_dry_run_is_default_and_never_calls_transport(tmp_path):
    sent = []
    g = SendGuard(sent.append)
    assert g.send(MSG, Approval("aaron", MSG.digest())) == "dry-run"
    assert sent == []


def test_real_send_requires_explicit_opt_in(tmp_path):
    g, sent = make(tmp_path, dry_run=False)
    assert g.send(MSG, Approval("aaron", MSG.digest())) == "sent"
    assert sent == [MSG]


def test_approval_is_single_use(tmp_path):
    g, _ = make(tmp_path, dry_run=False)
    ap = Approval("aaron", MSG.digest())
    g.send(MSG, ap)
    with pytest.raises(OutboundBlocked, match="already used"):
        g.send(MSG, ap)


def test_every_attempt_is_audited(tmp_path):
    g, _ = make(tmp_path, dry_run=False)
    with pytest.raises(OutboundBlocked):
        g.send(MSG)
    g.send(MSG, Approval("aaron", MSG.digest()))
    events = [json.loads(l)["event"] for l in (tmp_path / "audit.jsonl").read_text().splitlines()]
    assert events == ["blocked", "sent"]


def test_digest_is_unambiguous_across_field_boundaries():
    a = Message("ab", "c", "d")
    b = Message("a", "bc", "d")
    assert a.digest() != b.digest()
