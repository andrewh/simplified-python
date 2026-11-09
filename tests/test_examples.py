"""The programs in examples/ run, and conform to every banned rule in the registry.

Restricted-rule conditions are prose until the checker exists, so they are
reviewed by hand. Only banned constructs are checked mechanically here.
"""

import subprocess
import sys

import pytest

from simplified_python.registry import DEFAULT_ROOT, contains_construct, load, parse_example

EXAMPLES = DEFAULT_ROOT.parent / "examples"
NON_CONFORMING = {EXAMPLES / "rewrite" / "before.py"}
CONFORMING = sorted(set(EXAMPLES.rglob("*.py")) - NON_CONFORMING)
BANNED = [rule for rule in load().rules if rule.status == "banned"]


def run(path):
    result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, check=True)
    return result.stdout


def banned_in(path):
    tree = parse_example(path.read_text(encoding="utf-8"))
    return {rule.id for rule in BANNED if contains_construct(tree, rule.anchor)}


def test_examples_exist():
    assert len(CONFORMING) >= 3


@pytest.mark.parametrize("path", CONFORMING, ids=lambda path: str(path.relative_to(EXAMPLES)))
def test_example_has_no_banned_constructs(path):
    assert banned_in(path) == set()


@pytest.mark.parametrize("path", CONFORMING, ids=lambda path: str(path.relative_to(EXAMPLES)))
def test_example_runs_on_stock_python(path):
    assert run(path)


def test_rewrite_before_breaks_the_rules_it_cites():
    assert banned_in(EXAMPLES / "rewrite" / "before.py") == {"SP118", "SP208", "SP304", "SP601"}


def test_rewrite_preserves_behaviour():
    assert run(EXAMPLES / "rewrite" / "before.py") == run(EXAMPLES / "rewrite" / "after.py")
