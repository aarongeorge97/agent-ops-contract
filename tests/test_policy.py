from agentops import default_rules, lint_text, lint_tree
from agentops.policy import mask


def rules(**kw):
    return default_rules(**kw)


def names(findings):
    return {f.rule for f in findings}


def test_flags_external_email_but_allows_own_domain():
    text = "ping ops@acme.test and buyer@customer.example"
    f = lint_text(text, rules=default_rules(["acme.test"]))
    assert [x.rule for x in f] == ["email"]
    assert "buyer" not in str(f[0])  # masked


def test_phone_and_street_address():
    f = lint_text("call (555) 123-4567 at 1200 Main Street", rules=rules())
    assert names(f) == {"phone", "street-address"}


def test_secret_shapes():
    fake = "sk-" + "a" * 30
    f = lint_text(f"key={fake}", rules=rules())
    assert names(f) == {"secret"}
    assert fake not in str(f[0])


def test_cash_and_payroll_terms():
    f = lint_text("Cash balance is fine; payroll runs Friday; runway 9 months", rules=rules())
    assert names(f) == {"cash-balance", "payroll"}


def test_clean_text_has_no_findings():
    assert lint_text("Revenue, margin and lane volume are fine.", rules=rules()) == []


def test_mask_never_returns_long_values_in_full():
    assert mask("abcdefghijkl") == "abc…[12 chars]"
    assert mask("ab") == "ab"


def test_lint_tree_skips_unlisted_suffixes(tmp_path):
    (tmp_path / "page.html").write_text("mail a@b.example")
    (tmp_path / "image.png").write_bytes(b"a@b.example")
    f = lint_tree(tmp_path)
    assert [x.path for x in f] == ["page.html"]
