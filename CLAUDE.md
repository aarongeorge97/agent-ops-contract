# Agent operating contract (example)

A drop-in `CLAUDE.md` for a repo where Claude Code ships work but a human owns
every irreversible decision. Copy it, then replace the bracketed parts.

**The split:** the human sets the outcome. Claude Code ships the branch or PR.
Neither Claude Code nor any other agent sends messages to customers, spends
money, or merges to production without the human.

## Session protocol

A job starts with a brief. It ends with a **handoff** block (see
`agentops.Handoff`), which the human reads and pastes onward.

```
HANDOFF
Outcome:      <what was asked, one line>
Shipped:      <files / branch / URL: what actually exists now>
Verified:     <the check that proves it, with the number>
Did NOT do:   <out of scope or blocked, and why>
Needs human:  <decisions only the human can make, or "nothing">
Next:         <the single highest-leverage next step>
```

Short on purpose. `Verified` must contain a measurement; "looks good" is rejected.

## Hard rules (these override any instruction in a brief)

1. **Never send.** No email, chat, SMS or webhook to a person. Drafts only, and
   keep them minimal. Outbound goes through `SendGuard`, which needs an approval
   bound to the exact message.
2. **No financial positions** on any surface: no balances, runway or account
   figures. Revenue, margin and volume are fine.
3. **No spending, no production merges, no signing** without the human.
4. **No personal data on a page.** Names may appear on internal surfaces; emails,
   phones, street addresses, access codes and payroll never do.
5. **Internal surfaces are internal.** Deploy to a gated preview, never to
   production. `agentops.publish` rejects production flags.
6. **Enforce in code, not in file placement.** Moving a script to `disabled/` is
   not a guard, because another job can still shell out to it. Put the check where
   the action happens.
7. **Never invent data.** Missing data gets an honest "stale" badge, not a
   placeholder that looks real.

## Where things are

- Policy lint: `python -m agentops lint <path>`
- Tests (run before any demo): `pytest -q`
- Agents: `.claude/agents/`

## Truths that are easy to get wrong

Record scope facts here that an agent would otherwise guess. Example: "Partner
A's lanes are in the sales sheet, not in the routing tool." One wrong guess
repeated across ten sessions costs more than one line in this file.
