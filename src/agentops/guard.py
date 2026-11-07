"""SendGuard: the only door an agent can use to send anything outbound.

Design rules, each enforced in code rather than by convention:

* Dry-run is the default. A real send needs an explicit ``dry_run=False``.
* Approval is bound to the exact message. A human approves a digest of the
  recipient + subject + body; change one character and the approval is void.
* Approval is single-use. One yes does not become a standing permission.
* Every attempt, allowed or blocked, is appended to an audit log.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


class OutboundBlocked(Exception):
    """Raised when a send is refused. The message says why."""


@dataclass(frozen=True)
class Message:
    to: str
    subject: str
    body: str

    def digest(self) -> str:
        h = hashlib.sha256()
        for part in (self.to, self.subject, self.body):
            h.update(len(part).to_bytes(4, "big"))
            h.update(part.encode())
        return h.hexdigest()


@dataclass(frozen=True)
class Approval:
    approver: str
    digest: str  # digest of the message the human actually read


class SendGuard:
    def __init__(
        self,
        transport: Callable[[Message], None],
        *,
        dry_run: bool = True,
        audit_log: Path | None = None,
    ) -> None:
        self._transport = transport
        self._dry_run = dry_run
        self._audit = audit_log
        self._spent: set[str] = set()

    def _log(self, event: str, msg: Message, approver: str | None = None, reason: str = "") -> None:
        if not self._audit:
            return
        rec = {"ts": time.time(), "event": event, "to": msg.to, "digest": msg.digest(),
               "approver": approver, "reason": reason}
        with self._audit.open("a") as f:
            f.write(json.dumps(rec) + "\n")

    def send(self, msg: Message, approval: Approval | None = None) -> str:
        """Returns "sent" or "dry-run". Raises OutboundBlocked otherwise."""
        d = msg.digest()
        if approval is None:
            self._log("blocked", msg, reason="no approval")
            raise OutboundBlocked("no human approval attached")
        if approval.digest != d:
            self._log("blocked", msg, approval.approver, "digest mismatch")
            raise OutboundBlocked("approval does not match this exact message")
        if approval.digest in self._spent:
            self._log("blocked", msg, approval.approver, "approval reused")
            raise OutboundBlocked("approval already used")
        self._spent.add(approval.digest)
        if self._dry_run:
            self._log("dry-run", msg, approval.approver)
            return "dry-run"
        self._transport(msg)
        self._log("sent", msg, approval.approver)
        return "sent"
