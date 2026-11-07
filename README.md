# agent-ops-contract

**Rules for AI agents that live in code, not in a prompt.**

Four small, tested primitives for running Claude Code agents where a mistake reaches a customer or leaks a number, plus the `CLAUDE.md` contract and agent templates that go with them. Python 3.10+, standard library only.

```
 brief ──► agent ──► work ──► ┌─ policy lint ──► blocked / clean
                              ├─ SendGuard    ──► needs approval of THIS message
                              ├─ deploy guard ──► gated preview only, never prod
                              └─ Handoff      ──► six fields, `verified` needs a number
```

I built these while running agents against real operations (routing, customer reporting, internal dashboards). Each one exists because a rule written in prose was easy to route around. The code here is a clean rewrite with no company data. Background is in [docs/DESIGN.md](docs/DESIGN.md).

## What is in it

| Piece | What it guarantees |
|-------|--------------------|
| [`policy`](src/agentops/policy.py) | Finds emails, phones, street addresses, secrets, cash terms and payroll mentions. Findings are **masked**, so the scanner cannot become the leak. |
| [`guard`](src/agentops/guard.py) | `SendGuard` sends nothing unless a human approval is bound to the exact recipient, subject and body. Dry-run by default, single-use approvals, JSONL audit log. |
| [`deploy`](src/agentops/deploy.py) | Builds a bundle, adds noindex headers, lints it, and publishes to a gated preview. Production flags raise before any process starts. |
| [`handoff`](src/agentops/handoff.py) | A fixed six-field report. `verified` must contain a number, so "looks good" is rejected. |
| [`CLAUDE.md`](CLAUDE.md) | A drop-in operating contract: what the human owns, seven hard rules, the handoff protocol. |
| [`.claude/agents/`](.claude/agents) | Steward and spin-up agent templates that follow the contract. |

## Try it

```bash
pip install -e ".[dev]"
pytest -q                                   # 26 tests
python -m agentops lint examples/bundle --allow-domain acme.test
```

```python
from agentops import Message, Approval, SendGuard

sent = []
guard = SendGuard(sent.append)              # dry-run by default
msg = Message("buyer@example.test", "Update", "Draft body")

guard.send(msg)                             # OutboundBlocked: no human approval attached
guard.send(msg, Approval("aaron", msg.digest()))   # "dry-run", nothing leaves the machine
```

## Design stance

1. **Enforce in code, not in file placement.** Moving a script to `disabled/` is not a guard; another job can still call it.
2. **Approval is per action.** A yes to one draft is not a standing license.
3. **Safe path is the short path.** Dry-run is the default; sending takes a second, explicit opt-in.
4. **Never invent data.** A gap that says "stale" beats a placeholder that looks real.

## Limits

This narrows the blast radius of an honest, fallible agent. It is not a sandbox and does not stop an adversary with shell access. The lint rules are regexes, so they catch common shapes, not every leak; keep a human review on first publish.

## License

MIT
