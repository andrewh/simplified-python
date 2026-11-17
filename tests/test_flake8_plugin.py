"""Tests for the flake8 plugin adapter."""

import ast
import subprocess
import sys
from types import SimpleNamespace

import pytest

from simplified_python.check import check_source, default_rules_path, load_rules
from simplified_python.flake8_plugin import SimplifiedPythonChecker
from simplified_python.registry import DEFAULT_ROOT, load

ROOT = DEFAULT_ROOT.parent
BEFORE = ROOT / "examples" / "rewrite" / "before.py"
REGISTRY = load()
CHECKED = [rule for rule in REGISTRY.rules if rule.status != "allowed"]
RULES = load_rules(default_rules_path())


def plugin_results(code, restricted=False):
    SimplifiedPythonChecker.restricted = restricted
    try:
        checker = SimplifiedPythonChecker(ast.parse(code), "<string>")
        return [(line, column, message) for line, column, message, _ in checker.run()]
    finally:
        SimplifiedPythonChecker.restricted = False


def expected_results(code, restricted=False):
    return [
        (f.line, f.column - 1, f"{f.rule_id} {f.slug}: {f.message}")
        for f in check_source(code, RULES, restricted=restricted)
    ]


@pytest.mark.parametrize("restricted", [False, True], ids=["banned", "restricted"])
@pytest.mark.parametrize("rule", CHECKED, ids=lambda rule: rule.id)
def test_plugin_matches_checker_on_registry_examples(rule, restricted):
    for code in [*rule.violating, *rule.compliant]:
        assert plugin_results(code, restricted) == expected_results(code, restricted)


def test_plugin_matches_checker_on_rewrite_example():
    code = BEFORE.read_text(encoding="utf-8")
    assert plugin_results(code, restricted=True) == expected_results(code, restricted=True)


def test_version_mismatch_reports_sp000(monkeypatch):
    monkeypatch.setattr(sys, "version_info", SimpleNamespace(major=3, minor=13))
    results = plugin_results("from os import *\n")
    assert len(results) == 1
    assert results[0][2].startswith("SP000 ")


def run_flake8(tmp_path, source, *args):
    target = tmp_path / "sample.py"
    target.write_text(source, encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "flake8", "--select", "SP", *args, str(target)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_flake8_loads_the_plugin_and_honours_noqa(tmp_path):
    source = "from os import *\nif (n := 3):  # noqa: SP118\n    pass\n"
    result = run_flake8(tmp_path, source)
    assert result.returncode == 1
    codes = [line.split()[1] for line in result.stdout.splitlines()]
    assert codes == ["SP601"]


def test_flake8_restricted_option(tmp_path):
    source = "f = lambda x: x\n"
    assert run_flake8(tmp_path, source).returncode == 0
    result = run_flake8(tmp_path, source, "--sp-restricted")
    assert "SP116" in result.stdout


def test_flake8_reports_broken_condition_by_default(tmp_path):
    result = run_flake8(tmp_path, "a = b = 0\n")
    assert result.returncode == 1
    assert "SP203 single-target-assignment: " in result.stdout
