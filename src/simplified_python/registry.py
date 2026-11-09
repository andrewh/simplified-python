"""Load and validate the simplified-Python rule registry.

The registry under ``subset/`` is the single source of truth for the subset.
``validate`` collects every problem it finds instead of stopping at the first.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from simplified_python.check import Anchor, find_constructs

STATUSES = ("allowed", "restricted", "banned")
EXCLUSION_CATEGORIES = ("deprecated-placeholder", "alternate-parse-root", "opt-in-parse-flag")
RULE_ID = re.compile(r"SP\d{3}")
PRINCIPLE_ID = re.compile(r"P\d+")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "subset"

STR, INT, STR_LIST, TABLE, SCALAR = "string", "integer", "list of strings", "table", "string, integer or boolean"


@dataclass(frozen=True)
class Rule:
    id: str
    slug: str
    category: str
    construct: str
    anchor: Anchor
    status: str
    rationale: str
    principles: tuple[str, ...]
    condition: str | None
    replacement: str | None
    compliant: tuple[str, ...]
    violating: tuple[str, ...]
    source: str


@dataclass(frozen=True)
class Principle:
    id: str
    name: str
    statement: str
    cost: str


@dataclass(frozen=True)
class Exclusion:
    node: str
    category: str
    reason: str


@dataclass(frozen=True)
class Category:
    name: str
    title: str
    block: int
    file: str


@dataclass(frozen=True)
class Retired:
    id: str
    ruleset_version: int
    reason: str


@dataclass(frozen=True)
class Registry:
    root: Path
    python_version: str
    ruleset_version: int
    categories: tuple[Category, ...]
    principles: tuple[Principle, ...]
    exclusions: tuple[Exclusion, ...]
    rules: tuple[Rule, ...]
    published: tuple[str, ...]
    retired: tuple[Retired, ...]

    def rules_in(self, category: str) -> list[Rule]:
        return sorted((r for r in self.rules if r.category == category), key=lambda r: r.id)

    def principle(self, principle_id: str) -> Principle:
        return next(p for p in self.principles if p.id == principle_id)


@dataclass(frozen=True)
class ValidationError:
    file: str
    message: str
    rule: str | None = None
    field: str | None = None

    def __str__(self) -> str:
        where = ": ".join(part for part in (self.file, self.rule, self.field) if part)
        return f"{where}: {self.message}"


class RegistryError(Exception):
    def __init__(self, errors: list[ValidationError]):
        self.errors = errors
        super().__init__(format_errors(errors))


def grammar_leaves() -> dict[str, type[ast.AST]]:
    """Concrete AST node types: leaves of the ``ast.AST`` subclass tree."""
    leaves: dict[str, type[ast.AST]] = {}

    def walk(cls: type[ast.AST]) -> None:
        subclasses = cls.__subclasses__()
        if not subclasses:
            leaves[cls.__name__] = cls
        for sub in subclasses:
            walk(sub)

    walk(ast.AST)
    return dict(sorted(leaves.items()))


def contains_construct(tree: ast.AST, anchor: Anchor) -> bool:
    """Whether ``tree`` contains the construct ``anchor`` describes."""
    return next(find_constructs(tree, anchor), None) is not None


def parse_example(code: str) -> ast.Module:
    return ast.parse(code, mode="exec", feature_version=sys.version_info[:2])


class _Loader:
    def __init__(self, root: Path):
        self.root = root
        self.errors: list[ValidationError] = []

    def error(self, file: str, message: str, rule: str | None = None, field: str | None = None) -> None:
        self.errors.append(ValidationError(file, message, rule, field))

    def read(self, relative: str) -> dict | None:
        path = self.root / relative
        try:
            with path.open("rb") as handle:
                return tomllib.load(handle)
        except FileNotFoundError:
            self.error(relative, "file not found")
        except tomllib.TOMLDecodeError as exc:
            self.error(relative, f"invalid TOML: {exc}")
        return None

    def fields(self, file: str, rule: str | None, table: object, schema: dict[str, tuple[str, bool]], prefix: str = "") -> bool:
        """Check a table against ``{field: (type, required)}``; report every problem."""
        if not isinstance(table, dict):
            self.error(file, f"expected a table, got {type(table).__name__}", rule, prefix.rstrip(".") or None)
            return False
        ok = True
        for name, (kind, required) in schema.items():
            if name not in table:
                if required:
                    self.error(file, "required field is missing", rule, prefix + name)
                    ok = False
            elif not _is_type(table[name], kind):
                self.error(file, f"expected {kind}, got {_describe(table[name])}", rule, prefix + name)
                ok = False
        for name in table.keys() - schema.keys():
            self.error(file, "unknown field", rule, prefix + name)
            ok = False
        return ok

    def records(self, file: str, data: dict | None, key: str) -> list:
        if data is None:
            return []
        value = data.get(key, [])
        if not isinstance(value, list):
            self.error(file, f"expected an array of [[{key}]] tables", field=key)
            return []
        return value


def _is_type(value: object, kind: str) -> bool:
    match kind:
        case "string":
            return isinstance(value, str)
        case "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        case "list of strings":
            return isinstance(value, list) and all(isinstance(item, str) for item in value)
        case "table":
            return isinstance(value, dict)
        case _:
            return isinstance(value, (str, int, bool))


def _describe(value: object) -> str:
    return {str: "string", int: "integer", bool: "boolean", list: "array", dict: "table", float: "float"}.get(
        type(value), type(value).__name__
    )


MANIFEST_FIELDS = {"python_version", "ruleset_version", "category", "changelog"}
CATEGORY_SCHEMA = {"name": (STR, True), "title": (STR, True), "block": (INT, True), "file": (STR, True)}
CHANGELOG_SCHEMA = {"version": (INT, True), "summary": (STR, True)}
PRINCIPLE_SCHEMA = {"id": (STR, True), "name": (STR, True), "statement": (STR, True), "cost": (STR, True)}
EXCLUSION_SCHEMA = {"node": (STR, True), "category": (STR, True), "reason": (STR, True)}
RETIRED_SCHEMA = {"id": (STR, True), "ruleset_version": (INT, True), "reason": (STR, True)}
RULE_SCHEMA = {
    "id": (STR, True),
    "slug": (STR, True),
    "category": (STR, True),
    "construct": (STR, True),
    "anchor": (TABLE, True),
    "status": (STR, True),
    "rationale": (STR, True),
    "principles": (STR_LIST, False),
    "condition": (STR, False),
    "replacement": (STR, False),
    "compliant": (STR_LIST, True),
    "violating": (STR_LIST, False),
}
ANCHOR_SCHEMA = {"nodes": (STR_LIST, True), "attribute": (STR, False), "value": (SCALAR, False)}


def _load(root: Path) -> tuple[Registry | None, list[ValidationError], set[str]]:
    """Read every registry file. Returns the registry, schema errors, and ids of malformed rules."""
    loader = _Loader(root)
    manifest = loader.read("registry.toml")
    if manifest is None:
        return None, loader.errors, set()
    for name in manifest.keys() - MANIFEST_FIELDS:
        loader.error("registry.toml", "unknown field", field=name)
    python_version = manifest.get("python_version")
    ruleset_version = manifest.get("ruleset_version")
    if not isinstance(python_version, str) or not re.fullmatch(r"\d+\.\d+", python_version):
        loader.error("registry.toml", 'expected a "major.minor" string', field="python_version")
        python_version = ""
    if not _is_type(ruleset_version, INT):
        loader.error("registry.toml", "expected integer", field="ruleset_version")
        ruleset_version = 0

    categories = []
    for index, table in enumerate(loader.records("registry.toml", manifest, "category")):
        if loader.fields("registry.toml", None, table, CATEGORY_SCHEMA, f"category[{index}]."):
            categories.append(Category(**table))
    changelog = [
        table
        for index, table in enumerate(loader.records("registry.toml", manifest, "changelog"))
        if loader.fields("registry.toml", None, table, CHANGELOG_SCHEMA, f"changelog[{index}].")
    ]
    if ruleset_version and max((c["version"] for c in changelog), default=None) != ruleset_version:
        loader.error("registry.toml", "the latest [[changelog]] entry must record the current ruleset_version", field="changelog")

    principles = [
        Principle(**table)
        for index, table in enumerate(loader.records("principles.toml", loader.read("principles.toml"), "principle"))
        if loader.fields("principles.toml", table.get("id") if isinstance(table, dict) else None, table, PRINCIPLE_SCHEMA)
    ]

    exclusions = []
    for table in loader.records("exclusions.toml", loader.read("exclusions.toml"), "exclusion"):
        node = table.get("node") if isinstance(table, dict) else None
        if loader.fields("exclusions.toml", node, table, {**EXCLUSION_SCHEMA, "reason": (STR, False)}):
            exclusions.append(Exclusion(table["node"], table["category"], table.get("reason", "")))

    ledger = loader.read("published-ids.toml")
    published: list[str] = []
    retired: list[Retired] = []
    if ledger is not None:
        for name in ledger.keys() - {"ids", "retired"}:
            loader.error("published-ids.toml", "unknown field", field=name)
        ids = ledger.get("ids", [])
        if _is_type(ids, STR_LIST):
            published = ids
        else:
            loader.error("published-ids.toml", f"expected {STR_LIST}, got {_describe(ids)}", field="ids")
        for table in loader.records("published-ids.toml", ledger, "retired"):
            if loader.fields("published-ids.toml", table.get("id") if isinstance(table, dict) else None, table, RETIRED_SCHEMA):
                retired.append(Retired(**table))

    rules: list[Rule] = []
    malformed: set[str] = set()
    for category in categories:
        for index, table in enumerate(loader.records(category.file, loader.read(category.file), "rule")):
            label = table.get("id") if isinstance(table, dict) and isinstance(table.get("id"), str) else f"rule[{index}]"
            ok = loader.fields(category.file, label, table, RULE_SCHEMA)
            if not isinstance(table, dict):
                continue
            anchor_table = table.get("anchor")
            if isinstance(anchor_table, dict):
                ok = loader.fields(category.file, label, anchor_table, ANCHOR_SCHEMA, "anchor.") and ok
            else:
                anchor_table = {}
            if not ok:
                malformed.add(label)
            nodes = anchor_table.get("nodes")
            rules.append(
                Rule(
                    id=label,
                    slug=_get(table, "slug", STR, ""),
                    category=_get(table, "category", STR, category.name),
                    construct=_get(table, "construct", STR, ""),
                    anchor=Anchor(
                        tuple(nodes) if _is_type(nodes, STR_LIST) else (),
                        _get(anchor_table, "attribute", STR, None),
                        _get(anchor_table, "value", SCALAR, None),
                    ),
                    status=_get(table, "status", STR, ""),
                    rationale=_get(table, "rationale", STR, ""),
                    principles=tuple(_get(table, "principles", STR_LIST, [])),
                    condition=_get(table, "condition", STR, None),
                    replacement=_get(table, "replacement", STR, None),
                    compliant=tuple(_get(table, "compliant", STR_LIST, [])),
                    violating=tuple(_get(table, "violating", STR_LIST, [])),
                    source=category.file,
                )
            )
            if _get(table, "category", STR, category.name) != category.name:
                loader.error(category.file, f"category must be {category.name!r} to match the file it is declared in", label, "category")

    registry = Registry(
        root=root,
        python_version=python_version,
        ruleset_version=ruleset_version,
        categories=tuple(categories),
        principles=tuple(sorted(principles, key=lambda p: int(p.id[1:]) if PRINCIPLE_ID.fullmatch(p.id) else 0)),
        exclusions=tuple(exclusions),
        rules=tuple(sorted(rules, key=lambda r: r.id)),
        published=tuple(published),
        retired=tuple(retired),
    )
    return registry, loader.errors, malformed


def _get(table: dict, name: str, kind: str, default):
    value = table.get(name, default)
    return value if value is default or _is_type(value, kind) else default


def running_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def validate(root: Path = DEFAULT_ROOT, interpreter: str | None = None) -> list[ValidationError]:
    """Load and validate the registry at ``root``; return every error found."""
    return _validate(root, interpreter)[1]


def load(root: Path = DEFAULT_ROOT) -> Registry:
    """Load the registry, raising ``RegistryError`` with every error if it is invalid."""
    registry, errors = _validate(root, None)
    if errors:
        raise RegistryError(errors)
    return registry


def _validate(root: Path, interpreter: str | None) -> tuple[Registry | None, list[ValidationError]]:
    registry, errors, malformed = _load(Path(root))
    if registry is None:
        return None, errors
    v = _Validator(registry, errors, malformed)
    v.principles()
    v.identifiers()
    v.ledger()
    for rule in registry.rules:
        if rule.id not in malformed:
            v.status(rule)
            v.citations(rule)
    running = interpreter or running_version()
    if registry.python_version and running != registry.python_version:
        v.error(
            "registry.toml",
            f"registry declares Python {registry.python_version} but the running interpreter is Python {running}; "
            f"grammar validation needs Python {registry.python_version} and was not run",
            field="python_version",
        )
    elif registry.python_version:
        leaves = grammar_leaves()
        v.exclusions(leaves)
        resolved = [rule for rule in registry.rules if v.anchor(rule, leaves)]
        v.coverage(leaves, resolved)
        for rule in resolved:
            if rule.id not in malformed:
                v.examples(rule)
    return registry, errors


class _Validator:
    def __init__(self, registry: Registry, errors: list[ValidationError], malformed: set[str]):
        self.registry = registry
        self.errors = errors
        self.malformed = malformed

    def error(self, file: str, message: str, rule: str | None = None, field: str | None = None) -> None:
        self.errors.append(ValidationError(file, message, rule, field))

    def principles(self) -> None:
        seen: dict[str, str] = {}
        for principle in self.registry.principles:
            if not PRINCIPLE_ID.fullmatch(principle.id):
                self.error("principles.toml", "principle id must be P followed by digits", principle.id, "id")
            if principle.id in seen:
                self.error("principles.toml", "duplicate principle id", principle.id, "id")
            seen[principle.id] = principle.name

    def identifiers(self) -> None:
        by_id: dict[str, list[Rule]] = defaultdict(list)
        by_slug: dict[str, list[Rule]] = defaultdict(list)
        blocks = {c.name: c.block for c in self.registry.categories}
        retired = {r.id for r in self.registry.retired}
        for rule in self.registry.rules:
            if not RULE_ID.fullmatch(rule.id):
                if rule.id not in self.malformed:
                    self.error(rule.source, "id must be SP followed by three digits", rule.id, "id")
                continue
            by_id[rule.id].append(rule)
            if rule.slug:
                by_slug[rule.slug].append(rule)
                if not SLUG.fullmatch(rule.slug):
                    self.error(rule.source, "slug must be lowercase words joined by hyphens", rule.id, "slug")
            block = blocks.get(rule.category)
            if block is not None and int(rule.id[2]) != block:
                self.error(rule.source, f"id is outside the {rule.category} block; expected SP{block}xx", rule.id, "id")
            if rule.id in retired:
                self.error(rule.source, "id is retired; retired identifiers are never reassigned", rule.id, "id")
        for rule_id, rules in by_id.items():
            if len(rules) > 1:
                files = ", ".join(r.source for r in rules)
                self.error(rules[0].source, f"duplicate id {rule_id} declared in {files}", rule_id, "id")
        for slug, rules in by_slug.items():
            if len(rules) > 1:
                ids = ", ".join(r.id for r in rules)
                self.error(rules[0].source, f"duplicate slug {slug!r} used by {ids}", rules[0].id, "slug")

    def ledger(self) -> None:
        file = "published-ids.toml"
        active = {r.id for r in self.registry.rules if RULE_ID.fullmatch(r.id)}
        retired = [r.id for r in self.registry.retired]
        published = list(self.registry.published)
        for rule_id in sorted({i for i in published if published.count(i) > 1}):
            self.error(file, "identifier appears more than once in the ledger", rule_id, "ids")
        for rule_id in sorted({i for i in retired if retired.count(i) > 1}):
            self.error(file, "identifier is retired more than once", rule_id, "retired")
        for rule_id in dict.fromkeys(published):
            if rule_id not in active and rule_id not in retired:
                self.error(file, "published identifier is neither an active rule nor retired; retire it instead of deleting it", rule_id, "ids")
        for rule_id in sorted((active | set(retired)) - set(published)):
            self.error(file, "identifier is missing from the ledger; append it to ids", rule_id, "ids")

    def status(self, rule: Rule) -> None:
        if rule.status not in STATUSES:
            self.error(rule.source, f"status {rule.status!r} is not one of: {', '.join(STATUSES)}", rule.id, "status")
            return
        required = {"allowed": None, "restricted": "condition", "banned": "replacement"}[rule.status]
        for name in ("condition", "replacement"):
            present = getattr(rule, name) is not None
            if name == required and not present:
                self.error(rule.source, f"a {rule.status} rule must state its {name}", rule.id, name)
            elif name != required and present:
                hint = "; record a conditional permission as restricted" if rule.status == "allowed" else ""
                self.error(rule.source, f"a {rule.status} rule must not declare {name}{hint}", rule.id, name)

    def citations(self, rule: Rule) -> None:
        known = {p.id for p in self.registry.principles}
        if rule.status in ("restricted", "banned") and not rule.principles:
            self.error(rule.source, f"a {rule.status} rule must cite at least one principle", rule.id, "principles")
        for cited in rule.principles:
            if cited not in known:
                self.error(rule.source, f"unknown principle {cited!r}", rule.id, "principles")

    def anchor(self, rule: Rule, leaves: dict[str, type[ast.AST]]) -> bool:
        anchor, ok = rule.anchor, True
        if rule.id in self.malformed and not anchor.nodes:
            return False
        if not anchor.nodes:
            self.error(rule.source, "anchor must list at least one node type", rule.id, "anchor.nodes")
            return False
        for name in anchor.nodes:
            if name not in leaves:
                kind = "an abstract node type" if isinstance(getattr(ast, name, None), type) else "not an ast node type"
                self.error(rule.source, f"{name!r} is {kind} in Python {self.registry.python_version}", rule.id, "anchor.nodes")
                ok = False
            elif anchor.narrowed and anchor.attribute not in leaves[name]._fields:
                self.error(rule.source, f"{name} has no attribute {anchor.attribute!r}", rule.id, "anchor.attribute")
                ok = False
        if anchor.value is not None and not anchor.narrowed:
            self.error(rule.source, "anchor value requires an attribute", rule.id, "anchor.value")
            ok = False
        return ok

    def exclusions(self, leaves: dict[str, type[ast.AST]]) -> None:
        seen: set[str] = set()
        for exclusion in self.registry.exclusions:
            if not exclusion.reason.strip():
                self.error("exclusions.toml", "exclusion must give a reason", exclusion.node, "reason")
            if exclusion.category not in EXCLUSION_CATEGORIES:
                self.error("exclusions.toml", f"category must be one of: {', '.join(EXCLUSION_CATEGORIES)}", exclusion.node, "category")
            if exclusion.node not in leaves:
                self.error("exclusions.toml", "not a concrete ast node type", exclusion.node, "node")
            if exclusion.node in seen:
                self.error("exclusions.toml", "node is excluded more than once", exclusion.node, "node")
            seen.add(exclusion.node)
        for rule in self.registry.rules:
            for node in sorted(seen & set(rule.anchor.nodes)):
                self.error(rule.source, f"{node} is both excluded and anchored by this rule", rule.id, "anchor.nodes")

    def coverage(self, leaves: dict[str, type[ast.AST]], rules: list[Rule]) -> None:
        excluded = {e.node for e in self.registry.exclusions}
        base: dict[str, list[str]] = defaultdict(list)
        for rule in rules:
            if not rule.anchor.narrowed:
                for node in rule.anchor.nodes:
                    base[node].append(rule.id)
        required = [name for name in leaves if name not in excluded]
        missing = [name for name in required if not base[name]]
        doubled = [f"{name} ({', '.join(base[name])})" for name in required if len(base[name]) > 1]
        if missing:
            self.error("rules", f"{len(missing)} node type(s) have no unnarrowed rule: {', '.join(missing)}", field="coverage")
        if doubled:
            self.error("rules", f"{len(doubled)} node type(s) have more than one unnarrowed rule: {', '.join(doubled)}", field="coverage")

    def examples(self, rule: Rule) -> None:
        self.errors.extend(check_examples(rule))


def check_examples(rule: Rule) -> list[ValidationError]:
    """Check that a rule's examples parse and discriminate its anchored construct."""
    errors: list[ValidationError] = []
    if not rule.compliant:
        errors.append(ValidationError(rule.source, "rule must have at least one compliant example", rule.id, "compliant"))
    if rule.status in ("restricted", "banned") and not rule.violating:
        errors.append(ValidationError(rule.source, f"a {rule.status} rule must have at least one violating example", rule.id, "violating"))
    for kind, snippets in (("compliant", rule.compliant), ("violating", rule.violating)):
        for number, code in enumerate(snippets, start=1):
            label = f"{kind}[{number}]"
            try:
                tree = parse_example(code)
            except SyntaxError as exc:
                errors.append(ValidationError(rule.source, f"{kind} example {number} does not parse: {exc.msg} (line {exc.lineno})", rule.id, label))
                continue
            present = contains_construct(tree, rule.anchor)
            if kind == "violating" and not present:
                errors.append(ValidationError(rule.source, f"violating example {number} does not contain the anchored construct", rule.id, label))
            if kind == "compliant" and rule.status == "banned" and present:
                errors.append(ValidationError(rule.source, f"compliant example {number} contains the banned construct", rule.id, label))
    return errors


def format_errors(errors: list[ValidationError]) -> str:
    by_file: dict[str, list[ValidationError]] = defaultdict(list)
    for error in errors:
        by_file[error.file].append(error)
    lines = [f"{len(errors)} registry error(s):"]
    for file in sorted(by_file):
        lines.append(f"\n{file}")
        lines.extend("  " + ": ".join(p for p in (e.rule, e.field, e.message) if p) for e in by_file[file])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m simplified_python.registry", description=__doc__)
    parser.add_argument("--check", action="store_true", required=True, help="validate the registry and report every error")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="registry directory (default: subset/)")
    args = parser.parse_args(argv)
    registry, errors = _validate(args.root, None)
    if errors:
        print(format_errors(errors), file=sys.stderr)
        return 1
    print(f"registry OK: {len(registry.rules)} rules, ruleset version {registry.ruleset_version}, Python {registry.python_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
