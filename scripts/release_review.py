#!/usr/bin/env python3
"""Scan the working tree and every committed revision for private release terms."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterable


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True, errors="replace"
    )


def _terms_from_private_file(path: Path) -> list[str]:
    # Callers must never log, return, or otherwise expose these values.
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _line_hits(label: str, text: str, terms: Iterable[str]) -> set[str]:
    hits: set[str] = set()
    folded_terms = tuple(term.casefold() for term in terms)
    for number, line in enumerate(text.splitlines(), start=1):
        folded = line.casefold()
        if any(term in folded for term in folded_terms):
            hits.add(f"{label}:{number}")
    return hits


def scan(repo: Path, terms_path: Path) -> list[str]:
    terms = _terms_from_private_file(terms_path)
    hits: set[str] = set()
    current = _git(repo, "ls-files", "--cached", "--others", "--exclude-standard").splitlines()
    for relative in current:
        path = repo / relative
        if path.is_file() and ".git" not in path.parts:
            hits |= _line_hits(relative, path.read_text(encoding="utf-8", errors="replace"), terms)

    commits = _git(repo, "rev-list", "--all").splitlines()
    for commit in commits:
        names = _git(repo, "ls-tree", "-r", "--name-only", commit).splitlines()
        for relative in names:
            content = subprocess.run(
                ["git", "-C", str(repo), "show", f"{commit}:{relative}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
            ).stdout.decode("utf-8", errors="replace")
            hits |= _line_hits(f"history/{commit}/{relative}", content, terms)
    return sorted(hits)


def main() -> int:
    private_path = os.environ.get("RELEASE_REVIEW_TERMS")
    if not private_path:
        print("FAIL")
        print("RELEASE_REVIEW_TERMS:0")
        return 2
    hits = scan(Path.cwd(), Path(private_path))
    print("FAIL" if hits else "PASS")
    for hit in hits:
        print(hit)
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
