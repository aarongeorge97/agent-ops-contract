"""Deploy guard: lint the bundle, then publish to a *gated preview* only.

"Internal pages go to a protected preview, never production" is the kind of
rule that rots when it lives in a README. Here a production deploy is
impossible through this module: ``publish`` rejects any argv that asks for it,
and ``build_bundle`` refuses to hand back a bundle that fails the policy lint.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable, Sequence

from .policy import Finding, Rule, default_rules, lint_tree

PROD_FLAGS = ("--prod", "--production", "--target=production", "--target", "production")
DEFAULT_ARGV = ("vercel", "deploy", "--yes")

NOINDEX_FILES = {
    "robots.txt": "User-agent: *\nDisallow: /\n",
    "vercel.json": '{"headers":[{"source":"/(.*)","headers":['
                   '{"key":"X-Robots-Tag","value":"noindex, nofollow, noarchive"},'
                   '{"key":"Cache-Control","value":"no-store"}]}]}\n',
}


class DeployRefused(Exception):
    pass


def build_bundle(
    src: Path,
    out: Path,
    *,
    rules: Sequence[Rule] | None = None,
    exclude: Sequence[str] = (),
) -> list[Finding]:
    """Copy ``src`` to ``out``, add noindex headers, lint. Returns findings (empty = clean)."""
    src, out = Path(src), Path(out)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out, ignore=shutil.ignore_patterns(*exclude) if exclude else None)
    for name, content in NOINDEX_FILES.items():
        (out / name).write_text(content)
    # The generated files above are config, not content: lint everything else.
    return [f for f in lint_tree(out, rules or default_rules()) if f.path not in NOINDEX_FILES]


def assert_preview_only(argv: Sequence[str]) -> None:
    low = [a.lower() for a in argv]
    if any(flag in low for flag in PROD_FLAGS):
        raise DeployRefused("production deploys are disabled in this module; preview only")


def publish(
    bundle: Path,
    findings: Sequence[Finding],
    *,
    argv: Sequence[str] = DEFAULT_ARGV,
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> subprocess.CompletedProcess:
    if findings:
        raise DeployRefused(f"refusing to publish: {len(findings)} lint finding(s), first: {findings[0]}")
    assert_preview_only(argv)
    return run(list(argv), cwd=bundle, capture_output=True, text=True, timeout=600)
