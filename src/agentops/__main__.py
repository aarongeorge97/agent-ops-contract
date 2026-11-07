"""CLI:  python -m agentops lint PATH [--allow-domain example.com]

Exit 0 when clean, 1 when findings exist. Findings are masked.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .policy import default_rules, lint_tree


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="agentops")
    sub = ap.add_subparsers(dest="cmd", required=True)
    lint = sub.add_parser("lint", help="scan a file or directory for PII, secrets and cash terms")
    lint.add_argument("path", type=Path)
    lint.add_argument("--allow-domain", action="append", default=[], help="email domain to permit (repeatable)")
    args = ap.parse_args(argv)

    findings = lint_tree(args.path, default_rules(args.allow_domain))
    for f in findings:
        print(f)
    print(f"{'FAIL' if findings else 'OK'}: {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
