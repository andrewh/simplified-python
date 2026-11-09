"""Negative tests: each broken fixture fails with an error naming its file, rule, and field."""

import pytest

from simplified_python.registry import (
    Anchor,
    RegistryError,
    contains_construct,
    load,
    parse_example,
    running_version,
    validate,
)

IMPORTS = "rules/imports.toml"
LEDGER = "published-ids.toml"

# fixture name -> (file, rule, field, message fragment)
BROKEN = {
    "missing-field": (IMPORTS, "SP601", "rationale", "required field is missing"),
    "unknown-field": (IMPORTS, "SP601", "severity", "unknown field"),
    "wrong-type": (IMPORTS, "SP601", "principles", "expected list of strings, got string"),
    "anchor-unknown-node": (IMPORTS, "SP601", "anchor.nodes", "'StarImport' is not an ast node type"),
    "anchor-empty-nodes": (IMPORTS, "SP601", "anchor.nodes", "at least one node type"),
    "anchor-bad-attribute": (IMPORTS, "SP601", "anchor.attribute", "alias has no attribute 'level'"),
    "anchor-value-without-attribute": (IMPORTS, "SP601", "anchor.value", "requires an attribute"),
    "status-restricted-no-condition": (IMPORTS, "SP601", "condition", "restricted rule must state its condition"),
    "status-banned-no-replacement": (IMPORTS, "SP601", "replacement", "banned rule must state its replacement"),
    "status-allowed-with-condition": (IMPORTS, "SP601", "condition", "record a conditional permission as restricted"),
    "status-invalid": (IMPORTS, "SP601", "status", "not one of: allowed, restricted, banned"),
    "principle-none-cited": (IMPORTS, "SP601", "principles", "must cite at least one principle"),
    "principle-unknown": (IMPORTS, "SP601", "principles", "unknown principle 'P9'"),
    "id-bad-format": (IMPORTS, "SP61", "id", "SP followed by three digits"),
    "id-duplicate": ("rules/expressions.toml", "SP100", "id", "duplicate id SP100 declared in rules/expressions.toml, rules/imports.toml"),
    "id-outside-block": (IMPORTS, "SP142", "id", "outside the imports block; expected SP6xx"),
    "id-retired-reused": (IMPORTS, "SP601", "id", "retired identifiers are never reassigned"),
    "slug-duplicate": (IMPORTS, "SP601", "slug", "duplicate slug 'no-star-import' used by SP601, SP602"),
    "coverage-unclassified": ("rules", None, "coverage", "no unnarrowed rule: Interpolation, TemplateStr"),
    "coverage-doubled": ("rules", None, "coverage", "more than one unnarrowed rule: Import (SP100, SP602), alias (SP100, SP602)"),
    "exclusion-no-reason": ("exclusions.toml", "Suite", "reason", "must give a reason"),
    "exclusion-and-classified": ("rules/expressions.toml", "SP100", "anchor.nodes", "Global is both excluded and anchored"),
    "exclusion-unknown-category": ("exclusions.toml", "TypeIgnore", "category", "category must be one of"),
    "ledger-missing-rule": (LEDGER, "SP601", "ids", "missing from the ledger"),
    "ledger-orphan": (LEDGER, "SP650", "ids", "neither an active rule nor retired"),
    "ledger-retired-missing": (LEDGER, "SP650", "ids", "missing from the ledger"),
    "example-syntax-error": (IMPORTS, "SP601", "compliant[1]", "compliant example 1 does not parse"),
    "example-non-python-syntax": (IMPORTS, "SP601", "compliant[1]", "does not parse"),
    "example-violating-lacks-construct": (IMPORTS, "SP601", "violating[1]", "does not contain the anchored construct"),
    "example-compliant-contains-banned": (IMPORTS, "SP601", "compliant[1]", "contains the banned construct"),
    "example-banned-no-violating": (IMPORTS, "SP601", "violating", "banned rule must have at least one violating example"),
    "example-restricted-no-violating": (IMPORTS, "SP601", "violating", "restricted rule must have at least one violating example"),
    "category-mismatch": (IMPORTS, "SP601", "category", "must be 'imports'"),
    "changelog-stale": ("registry.toml", None, "changelog", "must record the current ruleset_version"),
}


def test_base_fixture_is_valid(make_registry):
    assert validate(make_registry()) == []


@pytest.mark.parametrize("name", sorted(BROKEN))
def test_broken_fixture_is_rejected(make_registry, name):
    file, rule, field, fragment = BROKEN[name]
    errors = validate(make_registry(name))
    matching = [e for e in errors if e.file == file and e.rule == rule and e.field == field and fragment in e.message]
    assert matching, f"expected {file}: {rule}: {field}: ...{fragment}... in:\n" + "\n".join(map(str, errors))
    for part in (file, field):
        assert part in str(matching[0])


def test_every_error_is_reported_not_just_the_first(make_registry, tmp_path):
    root = make_registry("missing-field")
    (root / "principles.toml").write_text((root / "principles.toml").read_text().replace('id = "P1"', 'id = "Q1"'))
    errors = validate(root)
    assert {e.field for e in errors} >= {"rationale", "id"}


def test_load_raises_with_every_error(make_registry):
    with pytest.raises(RegistryError) as raised:
        load(make_registry("missing-field"))
    assert "rules/imports.toml" in str(raised.value) and "SP601" in str(raised.value)


def test_narrowed_rules_coexist_with_a_base_rule(make_registry):
    assert validate(make_registry("coverage-narrowed-coexists")) == []


def test_excluded_placeholder_keeps_coverage_satisfied(make_registry):
    root = make_registry()
    assert "AugLoad" in (root / "exclusions.toml").read_text()
    assert "AugLoad" not in (root / "rules/expressions.toml").read_text()
    assert validate(root) == []


def test_interpreter_gate_fails_on_a_different_version(make_registry):
    errors = validate(make_registry(), interpreter="3.13")
    assert len(errors) == 1
    assert errors[0].field == "python_version"
    assert "declares Python 3.14" in errors[0].message and "Python 3.13" in errors[0].message


def test_interpreter_gate_reports_rather_than_skips(make_registry):
    assert validate(make_registry("coverage-unclassified"), interpreter="3.15")


def test_running_interpreter_matches_declared_version():
    assert running_version() == "3.14", "the test suite must run on the registry's declared Python version"


def test_star_import_anchor_value_discriminates():
    anchor = Anchor(("alias",), "name", "*")
    assert contains_construct(parse_example("from os import *\n"), anchor)
    assert not contains_construct(parse_example("from os import path\n"), anchor)


def test_unnarrowed_attribute_anchor_matches_when_non_empty():
    anchor = Anchor(("ImportFrom",), "level")
    assert contains_construct(parse_example("from . import x\n"), anchor)
    assert not contains_construct(parse_example("from os import path\n"), anchor)
