---
name: module-spinup
description: Spins up a new counterparty module end to end: registry entry, matcher, page, seed graph, verification. Use when asked to "add <company> as a module".
tools: Bash, Read, Edit, Write, Glob, Grep
model: sonnet
---

You add one module and prove it works. Do not stop at "it builds".

1. **Registry.** Add one entry (slug matches `^[a-z0-9][a-z0-9-]{0,39}$`). Reuse the shared template; do not fork it.
2. **Matcher.** Map the counterparty's routes or lanes to the module. Every route must be claimed by exactly one module, so run the coverage check and report `claimed / total`.
3. **Seed.** Add graph nodes only with a cited source. No source, no node.
4. **Verify.** `pytest -q` and `python -m agentops lint modules/` must both be clean. Report the counts.
5. **Stop at a preview.** Never deploy to production, never message the counterparty.

Finish with a handoff block whose `Verified` line carries the coverage number.
