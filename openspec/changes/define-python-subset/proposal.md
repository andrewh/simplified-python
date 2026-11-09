# Define the Simplified Python Subset

## Why

The repository names an idea — "a simplified subset of Python that is easy for humans to review" — but does not define it. Nothing downstream can be built (checker, CI gate, agent guidance, formatter) until the subset is pinned down precisely enough to be decided mechanically, construct by construct, with no room for taste.

Review cost, not writing cost, is the bottleneck this project targets. Full Python offers several spellings for the same behaviour and a number of constructs that force a reviewer to look away from the code under review (decorators, metaclasses, `*` imports, nested closures, chained comprehensions). A prose style guide cannot close that gap, because prose drifts from the tool that enforces it. This change therefore produces the subset definition as a single machine-readable source of truth from which the human-facing reference is generated.

## What Changes

- **Rule registry as the source of truth.** TOML files under `subset/rules/`, one record per construct, each anchored to a CPython AST node type (optionally narrowed to an attribute path), with a status of `allowed`, `restricted`, or `banned`, a rationale, and worked examples. TOML because `tomllib` is in the standard library, so reading the registry needs no dependency.
- **Numbered review principles.** A small, stable set of principles (local reasoning, one obvious spelling, no action at a distance, bounded reading cost). Every `restricted` or `banned` rule must cite at least one. This makes exclusions arguable on the record rather than a matter of preference.
- **Target grammar pinned to Python 3.14.** The subset only ever removes or narrows syntax. Every conforming program is a valid Python program with identical runtime semantics — no new syntax, no rewriting, no transpiler.
- **Exhaustive coverage guarantee.** Every construct reachable from `ast.parse(mode="exec")` on the target version is classified. A test enumerates the AST node classes live and fails on anything unclassified. Nodes that cannot appear (deprecated placeholders such as `AugLoad`, `Param`, `Suite`; alternate parse roots such as `Expression`) are listed in an exclusion file with a one-line justification per entry, so the exclusion list cannot quietly become an escape hatch.
- **Examples as executable fixtures.** Each rule carries compliant and violating snippets. Tests assert that every snippet parses, that violating snippets really contain the anchored construct, and that compliant snippets do not. The definition therefore verifies itself before a checker exists, and the same fixtures become the acceptance tests for the checker later.
- **Generated human reference.** `docs/subset.md` is produced from the registry and checked for staleness in CI, so the document a reviewer reads can never disagree with the data a tool consumes.
- **Minimal scaffolding.** A `pyproject.toml`, one package, and a test runner — the least needed to make the guarantees above executable.

Explicitly **not** in this change: the checker or CLI, autofix, formatting rules, severity or warning levels, restrictions on library and builtin use (`eval`, dynamic `getattr`, monkey-patching), and agent-facing prompt guidance. Each is a separate change that depends on this one.

## Capabilities

### New Capabilities

- `subset-rules`: the normative definition — rule record schema, construct anchors, the three statuses, the review principles rules must cite, stable rule identifiers, the exhaustive-coverage guarantee, example fixture validity, and registry versioning.
- `subset-reference`: the published human-facing reference generated from the registry — organisation by category, required content per rule entry, principle text, and the freshness guarantee.

### Modified Capabilities

None. This is the first change in the repository; `openspec/specs/` is empty.

## Impact

- **New files and directories:** `subset/rules/*.toml`, `subset/exclusions.toml`, `src/simplified_python/`, `docs/subset.md`, `tests/`, `pyproject.toml`.
- **Toolchain:** tests require Python 3.14 because coverage is computed from the live `ast` module; CI must pin that interpreter. No runtime dependencies.
- **README:** updated to point at the generated reference instead of describing the subset informally.
- **Downstream commitments:** rule identifiers become public API — reviewers will cite them in review comments and future tooling will emit them, so renaming a rule is a breaking change. The registry format becomes the interface the checker is written against.
- **Deliberately deferred risk:** conditions on `restricted` rules are recorded as prose plus a machine-readable anchor, not as an executable predicate. The checker must implement each condition in code, and the rule's examples are the contract that keeps the two in step.
