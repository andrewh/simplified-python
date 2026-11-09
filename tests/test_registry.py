"""Tests over the real registry under subset/."""

import pytest

from simplified_python.registry import (
    DEFAULT_ROOT,
    _load,
    check_examples,
    grammar_leaves,
    load,
    validate,
)

REGISTRY, _, _ = _load(DEFAULT_ROOT)


def test_grammar_enumeration_yields_119_leaves():
    leaves = grammar_leaves()
    assert len(leaves) == 119
    assert "expr" not in leaves and "stmt" not in leaves
    assert {"arguments", "comprehension", "match_case", "TemplateStr"} <= leaves.keys()


def test_registry_is_valid():
    errors = validate()
    assert errors == [], "\n".join(map(str, errors))


def test_every_reachable_node_is_classified_exactly_once():
    excluded = {e.node for e in REGISTRY.exclusions}
    counts = {name: 0 for name in grammar_leaves() if name not in excluded}
    for rule in REGISTRY.rules:
        if not rule.anchor.narrowed:
            for node in rule.anchor.nodes:
                counts[node] += 1
    assert [n for n, c in counts.items() if c == 0] == []
    assert [n for n, c in counts.items() if c > 1] == []
    assert len(counts) == 109


def test_versions_are_available_to_consumers():
    registry = load()
    assert registry.python_version == "3.14"
    assert isinstance(registry.ruleset_version, int) and registry.ruleset_version >= 1


@pytest.mark.parametrize("rule", REGISTRY.rules, ids=lambda rule: f"{rule.id}-{rule.slug}")
def test_rule_examples(rule):
    errors = check_examples(rule)
    assert errors == [], "\n".join(map(str, errors))


def test_registry_loads_with_standard_library_only():
    import ast
    import sys
    from pathlib import Path

    import simplified_python.registry as module

    tree = ast.parse(Path(module.__file__).read_text())
    imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imported |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert imported - {"__future__"} <= set(sys.stdlib_module_names)


def test_cited_principles_resolve_to_statements():
    for rule in REGISTRY.rules:
        for cited in rule.principles:
            assert REGISTRY.principle(cited).statement


@pytest.mark.parametrize("rule", REGISTRY.rules, ids=lambda rule: f"{rule.id}-{rule.slug}")
def test_compliant_examples_compile_on_stock_python(rule):
    for code in rule.compliant:
        compile(code, f"<{rule.id} compliant>", "exec")
