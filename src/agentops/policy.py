"""Policy lint: block PII, secrets and cash figures before anything leaves the machine.

The lint never echoes a full match. Findings carry a masked snippet so that a
CI log or an agent transcript cannot itself become the leak.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_SUFFIXES = (".html", ".json", ".md", ".txt", ".py", ".js", ".csv")


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]
    # Matches that also satisfy one of these are allowed (e.g. your own domain).
    allow: tuple[re.Pattern[str], ...] = ()


@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    snippet: str  # masked

    def __str__(self) -> str:
        return f"{self.path}: {self.rule} -> {self.snippet}"


def _c(p: str) -> re.Pattern[str]:
    return re.compile(p, re.IGNORECASE)


def email_rule(allowed_domains: Iterable[str] = ()) -> Rule:
    allow = tuple(_c(rf"@{re.escape(d)}$") for d in allowed_domains)
    return Rule("email", _c(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), allow)


STATIC_RULES: tuple[Rule, ...] = (
    Rule("phone", _c(r"\(\d{3}\)\s?\d{3}-\d{4}|\b\d{3}[-.]\d{3}[-.]\d{4}\b")),
    Rule(
        "street-address",
        _c(r"\b\d{1,5}\s+[A-Z][A-Za-z.]+\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Dr|Drive|Ln|Way|Pkwy|Pike)\b"),
    ),
    Rule(
        "secret",
        _c(
            r"sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}"
            r"|AIza[0-9A-Za-z_-]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}"
            r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
        ),
    ),
    Rule("cash-balance", _c(r"cash balance|bank balance|cash in bank|\brunway\b")),
    Rule("payroll", _c(r"\bpayroll\b")),
    Rule("access-code", _c(r"access code:\s*\d{4,}")),
)


def default_rules(allowed_email_domains: Iterable[str] = ()) -> tuple[Rule, ...]:
    return (email_rule(allowed_email_domains), *STATIC_RULES)


def mask(text: str) -> str:
    """Keep just enough to locate the match, never enough to reuse it."""
    text = text.strip()
    return text if len(text) <= 4 else f"{text[:3]}…[{len(text)} chars]"


def lint_text(text: str, path: str = "<text>", rules: Sequence[Rule] | None = None) -> list[Finding]:
    rules = default_rules() if rules is None else rules
    out: list[Finding] = []
    for rule in rules:
        for m in rule.pattern.finditer(text):
            hit = m.group(0)
            if any(a.search(hit) for a in rule.allow):
                continue
            out.append(Finding(path, rule.name, mask(hit)))
    return out


def lint_tree(
    root: Path,
    rules: Sequence[Rule] | None = None,
    suffixes: Sequence[str] = DEFAULT_SUFFIXES,
) -> list[Finding]:
    root = Path(root)
    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    out: list[Finding] = []
    for p in files:
        if p.suffix not in suffixes:
            continue
        out.extend(lint_text(p.read_text(errors="ignore"), str(p.relative_to(root) if root.is_dir() else p.name), rules))
    return out
