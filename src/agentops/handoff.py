"""Handoff: the fixed-shape report an agent owes at the end of a job.

A free-form summary lets an agent say "done" with nothing behind it. This
format forces each claim to carry its evidence, and it rejects a ``verified``
line that contains no measurement.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

MAX_LINE = 160


class InvalidHandoff(ValueError):
    pass


@dataclass(frozen=True)
class Handoff:
    outcome: str      # what was asked, one line
    shipped: str      # what actually exists now (files, branch, URL)
    verified: str     # the check that proves it, with the number
    did_not_do: str   # out of scope or blocked, and why
    needs_human: str  # decisions only the human can make, or "nothing"
    next_step: str    # the single highest-leverage next step

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if not value.strip():
                raise InvalidHandoff(f"{name} is empty")
            if "\n" in value.strip():
                raise InvalidHandoff(f"{name} must be one line")
            if len(value) > MAX_LINE:
                raise InvalidHandoff(f"{name} is {len(value)} chars; limit {MAX_LINE}")
        if not re.search(r"\d", self.verified):
            raise InvalidHandoff("verified must contain a number (a count, a measurement, an exit code)")

    def render(self) -> str:
        self.validate()
        rows = [
            ("Outcome", self.outcome),
            ("Shipped", self.shipped),
            ("Verified", self.verified),
            ("Did NOT do", self.did_not_do),
            ("Needs human", self.needs_human),
            ("Next", self.next_step),
        ]
        return "HANDOFF\n" + "\n".join(f"{k + ':':<13}{v}" for k, v in rows)
