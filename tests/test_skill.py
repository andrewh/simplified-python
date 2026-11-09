"""Tests for the generated agent skill."""

import re
import shutil
import subprocess
import sys

import pytest

import simplified_python.check as check_module
from simplified_python.reference import PRERELEASE_NOTICE, anchor_id
from simplified_python.registry import DEFAULT_ROOT, load
from simplified_python.skill import DEFAULT_OUTPUT, DEFAULT_TEMPLATE, main, outputs, render_skill

ROOT = DEFAULT_ROOT.parent
REGISTRY = load()
TEMPLATE = DEFAULT_TEMPLATE.read_text(encoding="utf-8")
SKILL = (DEFAULT_OUTPUT / "SKILL.md").read_text(encoding="utf-8")


def rules_with(status):
    return [rule for rule in REGISTRY.rules if rule.status == status]


def section(title):
    return SKILL.split(f"\n## {title}\n", 1)[1].split("\n## ", 1)[0]


def test_frontmatter_names_the_skill_and_when_to_use_it():
    match = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", SKILL)
    assert match and match.group(1) == "simplified-python"
    assert "Use when" in match.group(2) and "simplified Python" in match.group(2)


@pytest.mark.parametrize("rule", rules_with("banned"), ids=lambda rule: rule.id)
def test_banned_rules_are_listed_with_their_replacement(rule):
    banned = section("Banned")
    assert f"[{rule.id}](reference.md#{anchor_id(rule.id)}) `{rule.slug}`" in banned
    assert rule.replacement in banned


@pytest.mark.parametrize("rule", rules_with("restricted"), ids=lambda rule: rule.id)
def test_restricted_rules_are_listed_with_their_condition(rule):
    restricted = section("Restricted")
    assert f"[{rule.id}](reference.md#{anchor_id(rule.id)}) `{rule.slug}`" in restricted
    assert rule.condition in restricted


def test_allowed_rules_appear_only_as_slugs():
    allowed = section("Allowed")
    for rule in rules_with("allowed"):
        assert f"`{rule.slug}`" in allowed
        assert rule.id not in SKILL and rule.rationale not in SKILL
    assert "reference.md" in allowed


def test_principles_and_versions_are_stated():
    for principle in REGISTRY.principles:
        assert principle.id in SKILL and principle.statement in SKILL
    assert f"Rule-set version {REGISTRY.ruleset_version}" in SKILL
    assert f"Python {REGISTRY.python_version}" in SKILL


def test_workflow_guidance_is_present():
    for phrase in ("check.py", "--restricted", "by hand", "stop and ask", "# was SP118", "exits 1"):
        assert phrase in SKILL


def test_prerelease_notice_is_carried():
    assert "\n".join(PRERELEASE_NOTICE) in SKILL


def test_relative_links_resolve_inside_the_skill():
    reference = (DEFAULT_OUTPUT / "reference.md").read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", SKILL):
        path, _, fragment = target.partition("#")
        assert (DEFAULT_OUTPUT / path).is_file(), target
        if fragment:
            assert f'<a id="{fragment}"></a>' in reference, target


def test_the_skill_is_much_smaller_than_the_reference():
    assert len(SKILL) < len((DEFAULT_OUTPUT / "reference.md").read_text(encoding="utf-8")) / 3


def test_template_placeholders_are_all_filled():
    assert "{{" not in SKILL
    with pytest.raises(ValueError, match="placeholder"):
        render_skill(REGISTRY, TEMPLATE + "\n{{UNKNOWN}}\n")


def test_committed_skill_is_up_to_date():
    assert main(["--check"]) == 0


def test_generated_directory_matches_the_sources():
    files = outputs(REGISTRY, TEMPLATE, DEFAULT_OUTPUT)
    assert {p for p in DEFAULT_OUTPUT.rglob("*") if p.is_file()} == set(files)
    assert (DEFAULT_OUTPUT / "check.py").read_bytes() == open(check_module.__file__, "rb").read()


def test_two_runs_are_byte_identical():
    assert outputs(REGISTRY, TEMPLATE, DEFAULT_OUTPUT) == outputs(REGISTRY, TEMPLATE, DEFAULT_OUTPUT)


def test_rules_snapshot_carries_versions_and_only_restrictions():
    snapshot = check_module.load_rules(DEFAULT_OUTPUT / "rules.json")
    assert (snapshot.ruleset_version, snapshot.python_version) == (REGISTRY.ruleset_version, REGISTRY.python_version)
    assert {r.id for r in snapshot.rules} == {r.id for r in REGISTRY.rules if r.status != "allowed"}


def test_stale_and_stray_files_are_detected(tmp_path, capsys):
    out = tmp_path / "skill"
    shutil.copytree(DEFAULT_OUTPUT, out)
    args = ["--output", str(out), "--check"]
    assert main(args) == 0
    (out / "SKILL.md").write_text("edited by hand\n")
    assert main(args) == 1
    assert "SKILL.md is out of date" in capsys.readouterr().err
    assert main(["--output", str(out)]) == 0 and main(args) == 0
    (out / "stray.txt").write_text("x")
    assert main(args) == 1
    assert "stray.txt" in capsys.readouterr().err
    (out / "stray.txt").unlink()
    (out / "rules.json").unlink()
    assert main(args) == 1


def test_registry_change_makes_the_skill_stale(tmp_path, capsys):
    root = tmp_path / "subset"
    shutil.copytree(DEFAULT_ROOT, root)
    path = root / "rules" / "imports.toml"
    text = path.read_text()
    assert "Import the names you use explicitly" in text
    path.write_text(text.replace("Import the names you use explicitly", "Import names explicitly"))
    assert main(["--root", str(root), "--check"]) == 1
    assert "SKILL.md is out of date" in capsys.readouterr().err


def test_invalid_registry_writes_nothing(tmp_path, make_registry):
    out = tmp_path / "skill"
    assert main(["--root", str(make_registry("missing-field")), "--output", str(out)]) == 1
    assert not out.exists()


def test_copied_skill_works_from_another_location(tmp_path):
    copy = tmp_path / "agents" / "skills" / "simplified-python"
    shutil.copytree(DEFAULT_OUTPUT, copy)
    sample = tmp_path / "work" / "sample.py"
    sample.parent.mkdir()
    sample.write_text("from os import *\n")
    result = subprocess.run([sys.executable, str(copy / "check.py"), str(sample)], cwd=sample.parent, capture_output=True, text=True)
    assert result.returncode == 1 and "error SP601 no-star-import" in result.stdout
    for path in ("examples/before.py", "examples/after.py"):
        assert (copy / path).is_file()
    clean = subprocess.run([sys.executable, str(copy / "check.py"), str(copy / "examples" / "after.py")], capture_output=True, text=True)
    assert clean.returncode == 0
    flagged = subprocess.run([sys.executable, str(copy / "check.py"), str(copy / "examples" / "before.py")], capture_output=True, text=True)
    assert flagged.returncode == 1
