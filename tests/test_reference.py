"""Tests for the generated reference document."""

import re
import shutil

import pytest

from simplified_python.reference import (
    COMMAND,
    DEFAULT_OUTPUT,
    DEFAULT_README,
    PRERELEASE_NOTICE,
    SUMMARY_BEGIN,
    SUMMARY_END,
    generate,
    main,
    render,
    render_summary,
    splice_summary,
)
from simplified_python.registry import DEFAULT_ROOT, load


@pytest.fixture(scope="module")
def registry():
    return load()


@pytest.fixture(scope="module")
def document(registry):
    return render(registry)


def test_two_runs_are_byte_identical():
    first, _ = generate()
    second, _ = generate()
    assert first is not None and first.encode() == second.encode()


def test_record_order_in_files_does_not_change_output(tmp_path):
    root = tmp_path / "subset"
    shutil.copytree(DEFAULT_ROOT, root)
    for path in (root / "rules").glob("*.toml"):
        header, *records = path.read_text().split("\n[[rule]]\n")
        path.write_text("\n[[rule]]\n".join([header, *reversed(records)]))
    assert generate(root) == generate()


def test_generation_aborts_on_invalid_registry(tmp_path, make_registry):
    output = tmp_path / "subset.md"
    readme = tmp_path / "README.md"
    readme.write_text(f"{SUMMARY_BEGIN}\n{SUMMARY_END}\n")
    assert main(["--root", str(make_registry("missing-field")), "--output", str(output), "--readme", str(readme)]) == 1
    assert not output.exists()
    assert readme.read_text() == f"{SUMMARY_BEGIN}\n{SUMMARY_END}\n"


def test_banner_comes_first(document):
    head = "\n".join(document.splitlines()[:6])
    assert "do not edit" in head and COMMAND in head and "subset/" in head


def test_every_rule_has_an_entry_and_one_index_row(registry, document):
    for rule in registry.rules:
        assert document.count(f'<a id="{rule.id.lower()}"></a>') == 1
        assert document.count(f"| [{rule.id}](#{rule.id.lower()}) | `{rule.slug}` | {rule.status} |") == 1


def test_principles_precede_rules_and_are_complete(registry, document):
    first_rule = document.index('<a id="sp')
    for principle in registry.principles:
        position = document.index(f'<a id="{principle.id.lower()}"></a>')
        assert position < first_rule
        assert principle.statement in document and principle.cost in document


def test_principle_citations_link_to_principles(document):
    targets = set(re.findall(r'<a id="([a-z0-9]+)"></a>', document))
    links = set(re.findall(r"\]\(#([a-z0-9]+)\)", document))
    assert links and links <= targets


def test_examples_are_rendered_verbatim(registry, document):
    for rule in registry.rules:
        for code in rule.compliant + rule.violating:
            assert f"```python\n{code.rstrip(chr(10))}\n```" in document


def test_banned_entry_puts_violation_next_to_replacement(registry, document):
    for rule in registry.rules:
        if rule.status != "banned":
            continue
        entry = document[document.index(f'<a id="{rule.id.lower()}"></a>') :]
        violating = entry.index("Violating:")
        instead = entry.index(f"**Instead:** {rule.replacement}")
        compliant = entry.index("Compliant:")
        assert violating < instead < compliant


def test_restricted_entry_shows_condition(registry, document):
    for rule in registry.rules:
        if rule.status == "restricted":
            assert f"**Condition:** {rule.condition}" in document


def test_anchor_is_independent_of_rule_text(registry):
    rule = registry.rules[0]
    revised = type(registry)(
        **{**registry.__dict__, "rules": (type(rule)(**{**rule.__dict__, "rationale": "Changed.", "slug": "renamed"}), *registry.rules[1:])}
    )
    assert f'<a id="{rule.id.lower()}"></a>' in render(revised)


def test_committed_reference_is_up_to_date():
    expected, errors = generate()
    assert expected is not None, errors
    current = DEFAULT_OUTPUT.read_text(encoding="utf-8") if DEFAULT_OUTPUT.exists() else ""
    assert current == expected, f"docs/subset.md is out of date with the registry. Run `{COMMAND}` and commit the result."


def test_new_principle_appears_without_further_edits(tmp_path):
    root = tmp_path / "subset"
    shutil.copytree(DEFAULT_ROOT, root)
    with (root / "principles.toml").open("a") as handle:
        handle.write('\n[[principle]]\nid = "P9"\nname = "added"\nstatement = "A new principle."\ncost = "A new cost."\n')
    document, errors = generate(root)
    assert document is not None, errors
    assert '<a id="p9"></a>' in document and "A new principle." in document


def test_check_fails_when_reference_is_edited_by_hand(tmp_path):
    output = tmp_path / "subset.md"
    output.write_text(DEFAULT_OUTPUT.read_text() + "\nHand edit.\n")
    assert main(["--output", str(output), "--check"]) == 1


def test_check_fails_when_registry_changes_without_regeneration(tmp_path, capsys):
    root = tmp_path / "subset"
    shutil.copytree(DEFAULT_ROOT, root)
    path = root / "rules" / "imports.toml"
    path.write_text(path.read_text().replace("Import the names you use explicitly", "Import names explicitly"))
    assert main(["--root", str(root), "--output", str(DEFAULT_OUTPUT), "--check"]) == 1
    assert f"Run `{COMMAND}`" in capsys.readouterr().err


def test_check_passes_when_reference_matches():
    assert main(["--check"]) == 0


def test_readme_summary_lists_every_narrowing_rule_with_a_link(registry):
    summary = render_summary(registry)
    for rule in registry.rules:
        row = f"[{rule.id}](docs/subset.md#{rule.id.lower()}) `{rule.slug}`"
        assert (row in summary) == (rule.status != "allowed")
    assert summary.index("### Banned") < summary.index("### Restricted")


def test_readme_summary_is_spliced_between_markers():
    readme = f"intro\n{SUMMARY_BEGIN}\nold\n{SUMMARY_END}\noutro\n"
    assert splice_summary(readme, "new\n") == f"intro\n{SUMMARY_BEGIN}\nnew\n{SUMMARY_END}\noutro\n"


def test_readme_without_markers_is_rejected():
    with pytest.raises(ValueError, match="BEGIN GENERATED SUBSET SUMMARY"):
        splice_summary("no markers\n", "new\n")


def test_committed_readme_summary_is_up_to_date(registry):
    current = DEFAULT_README.read_text(encoding="utf-8")
    assert current == splice_summary(current, render_summary(registry)), (
        f"README.md summary is out of date with the registry. Run `{COMMAND}` and commit the result."
    )


def test_check_fails_when_readme_summary_is_edited_by_hand(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(DEFAULT_README.read_text().replace("### Banned", "### Forbidden"))
    assert main(["--readme", str(readme), "--check"]) == 1


def test_prerelease_notice_appears_in_reference_and_readme(document):
    notice = "\n".join(PRERELEASE_NOTICE)
    assert notice in document
    assert notice in DEFAULT_README.read_text(encoding="utf-8")
