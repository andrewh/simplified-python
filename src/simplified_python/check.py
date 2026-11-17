"""Report banned constructs, and broken restricted conditions, in Python files.

Standard library only. It reads a ``rules.json`` snapshot generated from the
registry, so this file runs on its own, for example from an agent skill:

    uv run --python 3.14 check.py [--restricted] FILE_OR_DIRECTORY...

Restricted rules listed in ``CONDITIONS`` have their condition checked in code:
an occurrence that breaks it is an error, and one that meets it is not reported.
The remaining restricted rules are listed with ``--restricted`` for manual review.

Exit status: 0 no violation, 1 a banned construct or broken condition found,
2 a file or the interpreter could not be checked.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

RULES_NAME = "rules.json"
FAILING = ("banned", "violated")
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
        label = "error" if self.status in FAILING else "review"
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


COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def _contains(node: ast.AST, kinds: type | tuple[type, ...]) -> bool:
    """Whether a node strictly inside ``node`` is one of ``kinds``."""
    return any(isinstance(inner, kinds) for inner in ast.walk(node) if inner is not node)


def _simple_comprehension(node: ast.AST) -> bool:
    if not isinstance(node, COMPREHENSIONS):
        return True  # the inner `comprehension` clause is judged with its enclosing comprehension
    return len(node.generators) == 1 and len(node.generators[0].ifs) <= 1 and not _contains(node, COMPREHENSIONS)


# Condition checks for restricted rules, by rule identifier. Each returns True when
# the matched node meets the rule's condition. Rules not listed here stay review items.
CONDITIONS: dict[str, Callable[[ast.AST], bool]] = {
    "SP110": lambda node: len(node.ops) == 1,
    "SP114": lambda node: not _contains(node, ast.IfExp),
    "SP117": _simple_comprehension,
    "SP203": lambda node: len(node.targets) == 1,
    "SP503": lambda node: len(node.bases) <= 1,
    "SP603": lambda node: node.level <= 1,
    "SP702": lambda node: node.type is not None,
}

Condition = Callable[[ast.AST], bool] | None
RuleIndex = dict[str, list[tuple[CheckRule, str, Condition]]]


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


def _build_rule_index(rules: Rules, restricted: bool) -> RuleIndex:
    """Index rules by node type. Checked restricted rules are always included;
    unchecked ones only when ``restricted`` asks for review items."""
    index: RuleIndex = {}
    for rule in rules.rules:
        condition = CONDITIONS.get(rule.id) if rule.status == "restricted" else None
        if rule.status == "banned":
            text = f"{rule.construct} Instead: {rule.replacement}"
        elif condition is not None:
            text = f"{rule.construct} Condition not met: {rule.condition}"
        elif rule.status == "restricted" and restricted:
            text = f"{rule.construct} Condition: {rule.condition} (not checked; verify by hand)"
        else:
            continue
        for node_type in rule.anchor.nodes:
            index.setdefault(node_type, []).append((rule, text, condition))
    return index


def _check_tree(tree: ast.AST, path: str, rule_index: RuleIndex) -> list[Finding]:
    findings: set[Finding] = set()
    stack: list[tuple[ast.AST, int, int]] = [(tree, 1, 1)]
    while stack:
        node, line, column = stack.pop()
        if hasattr(node, "lineno"):
            line, column = node.lineno, node.col_offset + 1
        stack.extend((child, line, column) for child in ast.iter_child_nodes(node))
        node_type = type(node).__name__
        if node_type not in rule_index:
            continue
        for rule, text, condition in rule_index[node_type]:
            if rule.anchor.narrowed:
                attr = getattr(node, rule.anchor.attribute, None)
                if not ((attr == rule.anchor.value) if rule.anchor.value is not None else bool(attr)):
                    continue
            if condition is None:
                findings.add(Finding(path, line, column, rule.id, rule.slug, rule.status, text))
            elif not condition(node):
                findings.add(Finding(path, line, column, rule.id, rule.slug, "violated", text))
    return sorted(findings)


def check_source(source: str, rules: Rules, path: str = "<string>", restricted: bool = False, rule_index: RuleIndex | None = None) -> list[Finding]:
    """Findings for ``source``, sorted by position. Raises ``SyntaxError`` if it does not parse."""
    tree = ast.parse(source, filename=path)
    if rule_index is None:
        rule_index = _build_rule_index(rules, restricted)
    return _check_tree(tree, path, rule_index)


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

    rule_index = _build_rule_index(rules, args.restricted)
    findings: list[Finding] = []
    problems = 0
    files = python_files(args.paths)
    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            findings += _check_tree(tree, str(path), rule_index)
        except (OSError, UnicodeDecodeError) as exc:
            print(f"{path}: cannot read: {exc}", file=sys.stderr)
            problems += 1
        except SyntaxError as exc:
            print(f"{path}:{exc.lineno or 1}:{exc.offset or 1}: syntax error: {exc.msg}", file=sys.stderr)
            problems += 1
    for finding in findings:
        print(finding)

    banned = sum(f.status == "banned" for f in findings)
    violated = sum(f.status == "violated" for f in findings)
    unchecked = sum(r.status == "restricted" and r.id not in CONDITIONS for r in rules.rules)
    note = (
        f"{unchecked} restricted condition(s) are not checked" if not args.restricted
        else "review entries need manual review"
    )
    print(
        f"{banned} banned construct(s) and {violated} broken restricted condition(s) in {len(files)} file(s); "
        f"{note}. Rule set version {rules.ruleset_version}."
    )
    return 2 if problems else 1 if banned or violated else 0


if __name__ == "__main__":
    sys.exit(main())
