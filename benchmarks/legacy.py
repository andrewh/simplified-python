"""Legacy checker implementation from git HEAD for benchmarking and regression tests.

This preserves the original multi-pass AST traversal implementation for comparison.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator

from simplified_python.check import Anchor, CheckRule, Finding, Rules


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
