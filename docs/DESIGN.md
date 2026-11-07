# Design notes

These primitives came out of running Claude Code agents against real operations
(routing, customer reporting, internal dashboards) where a mistake reaches a
customer or leaks a number. The rules are small. What mattered was where each one
lives.

## 1. A rule in prose is a suggestion

The first version of every rule was a sentence in `CLAUDE.md`. That works until a
second agent, a cron job or a sleepy refactor goes around it. Each rule here has
a code path that makes the violation impossible, or at least loud:

| Rule | Where it is enforced |
|------|----------------------|
| Never send | `SendGuard.send` raises without an approval bound to that exact message |
| No production deploy of internal pages | `assert_preview_only` rejects production flags before any process starts |
| No PII, secrets or cash figures on a page | `build_bundle` returns findings; `publish` refuses a non-empty list |
| Done means evidenced | `Handoff.validate` rejects a `verified` line with no number |

The corollary in the contract: **moving a script into a `disabled/` folder is not
a guard.** Another job can still shell out to it. Check at the point of action.

## 2. Approval is per action, not per session

A human saying "yes" to a draft must not become a standing license. `Approval`
carries a SHA-256 of the recipient, subject and body the person actually read.
Edit one character and it no longer matches. It is also single-use. The digest
length-prefixes each field, so `("ab","c")` and `("a","bc")` cannot collide.

## 3. Dry-run by default

The safe path is the short path: `SendGuard(transport)` does not send. Sending
takes a second, explicit `dry_run=False`. Tests then cannot message a real person
by accident. The transport is injected, so a test passes a list's `append`.

## 4. Lints must not become the leak

A scanner that prints the secret it found moves the secret into CI logs and agent
transcripts. Findings are masked (`abc…[34 chars]`), and tests assert the raw
value never appears in `str(finding)`.

## 5. Honest staleness over plausible placeholders

The contract's last rule, "never invent data", is the one agents break most
politely. A fabricated number that looks real is worse than a gap that says it is
stale. The handoff format applies the same pressure to the agent's own claims.

## What this is not

It is not a sandbox and it does not stop a determined adversary with shell access.
It narrows the blast radius of an honest-but-fallible agent and makes each
near-miss visible in an audit log. The lint rules are regexes: they catch the
common shapes, not every possible leak, so keep a human review on first publish.
