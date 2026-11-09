"""Report banned constructs from the simplified-Python subset in Python files.

Standard library only. It reads a ``rules.json`` snapshot generated from the
registry, so this file runs on its own, for example from an agent skill:

    uv run --python 3.14 check.py [--restricted] FILE_OR_DIRECTORY...

Exit status: 0 no banned construct, 1 banned construct found, 2 a file or the
interpreter could not be checked. Restricted conditions are not checked.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

RULES_NAME = "rules.json"
SNAPSHOT = Path(__file__).resolve().parents[2] / "skills" / "simplified-python" / RULES_NAME


@dataclass(frozen=True)
class Anchor:
    nodes: tuple[str, ...]
    attribute: str | None = None
    value: str | int | bool | None = None

    @property
    def narrowed(self) -> bool:
        return self.attribute is not None


@dataclass(frozen=True)
class CheckRule:
    id: str
    slug: str
    status: str
    construct: str
    anchor: Anchor
    condition: str | None = None
    replacement: str | None = None


@dataclass(frozen=True)
class Rules:
    ruleset_version: int
    python_version: str
    rules: tuple[CheckRule, ...]


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    column: int
    rule_id: str
    slug: str
    status: str
    message: str

    def __str__(self) -> str:
        label = "error" if self.status == "banned" else "review"
        return f"{self.path}:{self.line}:{self.column}: {label} {self.rule_id} {self.slug}: {self.message}"


def find_constructs(tree: ast.AST, anchor: Anchor) -> Iterator[tuple[ast.AST, int, int]]:
    """Yield ``(node, line, column)`` for each construct ``anchor`` describes.

    Nodes without a position (contexts, operators) take the nearest enclosing one.
    """
    stack: list[tuple[ast.AST, int, int]] = [(tree, 1, 1)]
    while stack:
        node, line, column = stack.pop()
        if hasattr(node, "lineno"):
            line, column = node.lineno, node.col_offset + 1
        stack.extend((child, line, column) for child in ast.iter_child_nodes(node))
        if type(node).__name__ not in anchor.nodes:
            continue
        if not anchor.narrowed:
            yield node, line, column
            continue
        attr = getattr(node, anchor.attribute, None)
        if (attr == anchor.value) if anchor.value is not None else bool(attr):
            yield node, line, column


def load_rules(path: Path) -> Rules:
    data = json.loads(path.read_text(encoding="utf-8"))
    rules = tuple(
        CheckRule(
            id=r["id"],
            slug=r["slug"],
            status=r["status"],
            construct=r["construct"],
            anchor=Anchor(tuple(r["anchor"]["nodes"]), r["anchor"].get("attribute"), r["anchor"].get("value")),
            condition=r.get("condition"),
            replacement=r.get("replacement"),
        )
        for r in data["rules"]
    )
    return Rules(data["ruleset_version"], data["python_version"], rules)


def check_source(source: str, rules: Rules, path: str = "<string>", restricted: bool = False) -> list[Finding]:
    """Findings for ``source``, sorted by position. Raises ``SyntaxError`` if it does not parse."""
    tree = ast.parse(source, filename=path)
    wanted = ("banned", "restricted") if restricted else ("banned",)
    findings: set[Finding] = set()
    for rule in rules.rules:
        if rule.status not in wanted:
            continue
        text = f"{rule.construct} Instead: {rule.replacement}" if rule.status == "banned" else (
            f"{rule.construct} Condition: {rule.condition} (not checked; verify by hand)"
        )
        for _, line, column in find_constructs(tree, rule.anchor):
            findings.add(Finding(path, line, column, rule.id, rule.slug, rule.status, text))
    return sorted(findings)


def python_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        files.extend(sorted(path.rglob("*.py")) if path.is_dir() else [path])
    return files


def default_rules_path() -> Path:
    beside = Path(__file__).resolve().with_name(RULES_NAME)
    return beside if beside.exists() else SNAPSHOT


def main(argv: list[str] | None = None, interpreter: str | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="+", type=Path, help="Python files or directories to check")
    parser.add_argument("--restricted", action="store_true", help="also list restricted constructs for manual review")
    parser.add_argument("--rules", type=Path, default=None, help=f"rules snapshot (default: {RULES_NAME} beside this file)")
    args = parser.parse_args(argv)

    try:
        rules = load_rules(args.rules or default_rules_path())
    except (OSError, ValueError, KeyError) as exc:
        print(f"cannot read the rules snapshot: {exc}", file=sys.stderr)
        return 2
    running = interpreter or f"{sys.version_info.major}.{sys.version_info.minor}"
    if running != rules.python_version:
        print(
            f"rules are for Python {rules.python_version} but this is Python {running}; nothing was checked. "
            f"Run with `uv run --python {rules.python_version} ...`.",
            file=sys.stderr,
        )
        return 2

    findings: list[Finding] = []
    problems = 0
    files = python_files(args.paths)
    for path in files:
        try:
            findings += check_source(path.read_text(encoding="utf-8"), rules, str(path), args.restricted)
        except (OSError, UnicodeDecodeError) as exc:
            print(f"{path}: cannot read: {exc}", file=sys.stderr)
            problems += 1
        except SyntaxError as exc:
            print(f"{path}:{exc.lineno or 1}:{exc.offset or 1}: syntax error: {exc.msg}", file=sys.stderr)
            problems += 1
    for finding in findings:
        print(finding)

    banned = sum(f.status == "banned" for f in findings)
    note = "restricted conditions are not checked" if not args.restricted else "restricted entries need manual review"
    print(f"{banned} banned construct(s) in {len(files)} file(s); {note}. Rule set version {rules.ruleset_version}.")
    return 2 if problems else 1 if banned else 0


if __name__ == "__main__":
    sys.exit(main())
