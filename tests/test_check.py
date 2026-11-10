"""Tests for the banned-construct checker."""

import json
import shutil
import subprocess
import sys

import pytest

import simplified_python.check as check_module
from simplified_python.check import Rules, check_source, load_rules, main
from simplified_python.registry import DEFAULT_ROOT, load
from benchmarks.legacy import check_source as check_source_legacy

ROOT = DEFAULT_ROOT.parent
EXAMPLES = ROOT / "examples"
BEFORE = EXAMPLES / "rewrite" / "before.py"
REGISTRY = load()
BANNED = [rule for rule in REGISTRY.rules if rule.status == "banned"]
RESTRICTED = [rule for rule in REGISTRY.rules if rule.status == "restricted"]


def write_rules(path):
    rules = [
        {
            "id": rule.id,
            "slug": rule.slug,
            "status": rule.status,
            "construct": rule.construct,
            "condition": rule.condition,
            "replacement": rule.replacement,
            "anchor": {
                key: value
                for key, value in (("nodes", list(rule.anchor.nodes)), ("attribute", rule.anchor.attribute), ("value", rule.anchor.value))
                if value is not None
            },
        }
        for rule in REGISTRY.rules
        if rule.status != "allowed"
    ]
    path.write_text(json.dumps({"ruleset_version": REGISTRY.ruleset_version, "python_version": REGISTRY.python_version, "rules": rules}))
    return path


@pytest.fixture(scope="module")
def rules(tmp_path_factory) -> Rules:
    return load_rules(write_rules(tmp_path_factory.mktemp("rules") / "rules.json"))


@pytest.fixture
def rules_file(tmp_path):
    return write_rules(tmp_path / "rules.json")


def ids(findings):
    return {finding.rule_id for finding in findings}


@pytest.mark.parametrize("rule", BANNED, ids=lambda rule: rule.id)
def test_violating_examples_are_flagged(rule, rules):
    for code in rule.violating:
        assert rule.id in ids(check_source(code, rules))


@pytest.mark.parametrize("rule", BANNED, ids=lambda rule: rule.id)
def test_compliant_examples_do_not_trigger_their_own_rule(rule, rules):
    for code in rule.compliant:
        assert rule.id not in ids(check_source(code, rules))


def test_finding_has_position_rule_and_replacement(rules):
    (finding,) = check_source("import os\n\nfrom os import *\n", rules, "mod.py")
    assert (finding.path, finding.line, finding.column, finding.rule_id) == ("mod.py", 3, 16, "SP601")
    assert "Instead:" in str(finding) and "mod.py:3:16: error SP601 " in str(finding)


def test_every_occurrence_is_reported_in_order(rules):
    findings = check_source("from a import *\nx = 1\nfrom b import *\nfrom c import *\n", rules)
    assert [(f.rule_id, f.line) for f in findings] == [("SP601", 1), ("SP601", 3), ("SP601", 4)]


def test_nodes_without_position_inherit_the_enclosing_one(rules):
    rule = check_module.CheckRule("SPX", "x", "banned", "c", check_module.Anchor(("Store",)), replacement="r")
    (finding,) = check_source("\n\nx = 1\n", Rules(1, "3.14", (rule,)))
    assert (finding.line, finding.column) == (3, 1)


def test_restricted_are_hidden_by_default_and_listed_on_request(rules):
    code = "f = lambda x: x\n"
    assert check_source(code, rules) == []
    finding = next(f for f in check_source(code, rules, restricted=True) if f.slug == "lambda-as-argument")
    assert finding.status == "restricted" and "not checked" in finding.message


def test_cli_exit_codes(rules_file, tmp_path, capsys):
    clean = tmp_path / "clean.py"
    clean.write_text("x = 1\n")
    bad = tmp_path / "bad.py"
    bad.write_text("from os import *\n")
    broken = tmp_path / "broken.py"
    broken.write_text("def (:\n")
    base = ["--rules", str(rules_file)]
    assert main([str(clean), *base]) == 0
    assert main([str(bad), *base]) == 1
    assert "bad.py:1:16: error SP601" in capsys.readouterr().out
    assert main([str(broken), *base]) == 2
    assert "syntax error" in capsys.readouterr().err
    assert main([str(bad), str(broken), *base]) == 2
    assert main([str(tmp_path / "missing.py"), *base]) == 2


def test_cli_restricted_does_not_change_exit_status(rules_file, tmp_path, capsys):
    path = tmp_path / "lam.py"
    path.write_text("f = lambda x: x\n")
    assert main([str(path), "--restricted", "--rules", str(rules_file)]) == 0
    assert "review SP" in capsys.readouterr().out
    assert main([str(path), "--rules", str(rules_file)]) == 0
    assert "review" not in capsys.readouterr().out


def test_wrong_interpreter_checks_nothing(rules_file, tmp_path, capsys):
    bad = tmp_path / "bad.py"
    bad.write_text("from os import *\n")
    assert main([str(bad), "--rules", str(rules_file)], interpreter="3.12") == 2
    err = capsys.readouterr().err
    assert "3.14" in err and "3.12" in err and "nothing was checked" in err


def test_directories_are_searched_recursively_in_order(rules_file, tmp_path, capsys):
    (tmp_path / "pkg" / "sub").mkdir(parents=True)
    (tmp_path / "pkg" / "b.py").write_text("from b import *\n")
    (tmp_path / "pkg" / "sub" / "a.py").write_text("from a import *\n")
    (tmp_path / "pkg" / "notes.txt").write_text("from n import *\n")
    assert main([str(tmp_path / "pkg"), "--rules", str(rules_file)]) == 1
    lines = [line for line in capsys.readouterr().out.splitlines() if "error" in line]
    assert [line.split(":")[0].rsplit("/", 1)[-1] for line in lines] == ["b.py", "a.py"]


def test_missing_rules_snapshot_is_an_error(tmp_path, capsys):
    assert main([str(tmp_path), "--rules", str(tmp_path / "nope.json")]) == 2


def test_conforming_examples_are_clean(rules):
    for path in sorted(EXAMPLES.rglob("*.py")):
        if path != BEFORE:
            assert check_source(path.read_text(), rules, str(path)) == [], path


def test_before_example_breaks_exactly_the_cited_rules(rules):
    assert ids(check_source(BEFORE.read_text(), rules, str(BEFORE))) == {"SP118", "SP208", "SP304", "SP601"}


def test_checker_runs_outside_the_repository(rules_file, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    shutil.copy(check_module.__file__, outside / "check.py")
    shutil.copy(rules_file, outside / "rules.json")
    sample = outside / "sample.py"
    sample.write_text("from os import *\n")
    result = subprocess.run([sys.executable, "check.py", "sample.py"], cwd=outside, capture_output=True, text=True)
    assert result.returncode == 1
    assert "sample.py:1:16: error SP601" in result.stdout


def test_checker_imports_only_the_standard_library():
    import ast
    from pathlib import Path

    tree = ast.parse(Path(check_module.__file__).read_text())
    imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert imported - {"__future__"} <= set(sys.stdlib_module_names)


def test_optimized_matches_legacy_on_all_examples(rules):
    for path in sorted(EXAMPLES.rglob("*.py")):
        if path != BEFORE:
            source = path.read_text(encoding="utf-8")
            legacy = check_source_legacy(source, rules, str(path))
            optimized = check_source(source, rules, str(path))
            assert legacy == optimized, f"Mismatch on {path}"


def test_optimized_matches_legacy_on_before_example(rules):
    source = BEFORE.read_text(encoding="utf-8")
    legacy = check_source_legacy(source, rules, str(BEFORE))
    optimized = check_source(source, rules, str(BEFORE))
    assert legacy == optimized


def test_optimized_matches_legacy_on_violating_examples(rules):
    for rule in BANNED:
        for code in rule.violating:
            legacy = check_source_legacy(code, rules)
            optimized = check_source(code, rules)
            assert legacy == optimized, f"Mismatch on {rule.id} violating example"


def test_optimized_matches_legacy_on_compliant_examples(rules):
    for rule in BANNED:
        for code in rule.compliant:
            legacy = check_source_legacy(code, rules)
            optimized = check_source(code, rules)
            assert legacy == optimized, f"Mismatch on {rule.id} compliant example"


def test_optimized_matches_legacy_restricted_mode(rules):
    code = "f = lambda x: x\n"
    legacy = check_source_legacy(code, rules, restricted=True)
    optimized = check_source(code, rules, restricted=True)
    assert legacy == optimized


def test_optimized_preserves_order_and_deduplication(rules):
    source = "from a import *\nx = 1\nfrom b import *\nfrom c import *\n"
    legacy = check_source_legacy(source, rules)
    optimized = check_source(source, rules)
    assert legacy == optimized
    assert [(f.line, f.column) for f in optimized] == [(f.line, f.column) for f in legacy]


def test_optimized_handles_nodes_without_position(rules):
    rule = check_module.CheckRule("SPX", "x", "banned", "c", check_module.Anchor(("Store",)), replacement="r")
    custom_rules = Rules(1, "3.14", (rule,))
    source = "\n\nx = 1\n"
    legacy = check_source_legacy(source, custom_rules)
    optimized = check_source(source, custom_rules)
    assert legacy == optimized
    assert len(optimized) == 1
    assert optimized[0].line == 3 and optimized[0].column == 1


def test_optimized_narrowed_anchor_matching(rules):
    source = "x = 1\ny: int = 2\n"
    legacy = check_source_legacy(source, rules)
    optimized = check_source(source, rules)
    assert legacy == optimized
