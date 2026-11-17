"""flake8 plugin that reports simplified-Python rule violations.

A thin adapter over ``simplified_python.check``: the rule logic and the rules
snapshot are shared, so flake8 and ``check.py`` always report the same findings.

Codes are the registry identifiers (``SP118`` and so on). Banned constructs are
always reported. Pass ``--sp-restricted`` to also report restricted constructs
for manual review. ``SP000`` means the interpreter does not match the rule set's
Python version, so nothing was checked.
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterator
from importlib.metadata import version

from simplified_python.check import CheckRule, Rules, _build_rule_index, _check_tree, default_rules_path, load_rules

Index = dict[str, list[tuple[CheckRule, str]]]


class SimplifiedPythonChecker:
    name = "simplified-python"
    version = version("simplified-python")

    restricted = False
    _rules: Rules | None = None
    _indexes: dict[bool, Index] = {}

    def __init__(self, tree: ast.AST, filename: str) -> None:
        self.tree = tree
        self.filename = filename

    @classmethod
    def add_options(cls, manager) -> None:
        manager.add_option(
            "--sp-restricted",
            action="store_true",
            parse_from_config=True,
            help="also report restricted simplified-Python constructs for manual review",
        )

    @classmethod
    def parse_options(cls, options) -> None:
        cls.restricted = options.sp_restricted

    @classmethod
    def rules(cls) -> Rules:
        if cls._rules is None:
            cls._rules = load_rules(default_rules_path())
        return cls._rules

    @classmethod
    def rule_index(cls) -> Index:
        if cls.restricted not in cls._indexes:
            cls._indexes[cls.restricted] = _build_rule_index(cls.rules(), cls.restricted)
        return cls._indexes[cls.restricted]

    def run(self) -> Iterator[tuple[int, int, str, type]]:
        rules = self.rules()
        running = f"{sys.version_info.major}.{sys.version_info.minor}"
        if running != rules.python_version:
            yield 1, 0, f"SP000 rules are for Python {rules.python_version} but flake8 runs on {running}; nothing was checked", type(self)
            return
        for finding in _check_tree(self.tree, self.filename, self.rule_index()):
            yield finding.line, finding.column - 1, f"{finding.rule_id} {finding.slug}: {finding.message}", type(self)
