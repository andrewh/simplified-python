# Tasks: Define the Simplified Python Subset

Order matters. The validator and its tests are built **before** the rules are authored, so that authoring 50-odd rules is guided by machine feedback rather than by proofreading.

## 1. Scaffolding

- [x] 1.1 Add `pyproject.toml`: project name `simplified-python`, `requires-python = ">=3.14"`, no runtime dependencies, pytest in a `dev` dependency group (`[dependency-groups]`, installed by `uv sync`), `src/` layout
- [x] 1.2 Create `src/simplified_python/__init__.py` and an empty `tests/` package
- [x] 1.3 Confirm `python -m pytest` runs green on a single placeholder test, then record the commands in `AGENTS.md`

## 2. Registry metadata and record shape

- [x] 2.1 Write `subset/registry.toml`: `python_version = "3.14"`, `ruleset_version`, and the ordered category list with each category's identifier block (`expressions` = SP1xx, `statements` = SP2xx, `control-flow` = SP3xx, `functions` = SP4xx, `classes` = SP5xx, `imports` = SP6xx, `exceptions` = SP7xx, `async` = SP8xx, `typing` = SP9xx) and its source file
- [x] 2.2 Write `subset/principles.toml` with the review principles (local reasoning, one obvious spelling, no action at a distance, bounded reading cost), each with a stable identifier and the review cost it addresses
- [x] 2.3 Write `subset/exclusions.toml` covering the 10 unreachable leaf nodes, each with a reason and a category: deprecated placeholders (`AugLoad`, `AugStore`, `Param`, `Suite`, `Index`, `ExtSlice`), alternate parse roots (`Interactive`, `Expression`, `FunctionType`), opt-in parse flag (`TypeIgnore`)
- [x] 2.4 Create `subset/published-ids.toml` as the append-only identifier ledger, with its structure and append-only intent stated in a header comment
- [x] 2.5 Author one exemplar rule in `subset/rules/imports.toml` — `from x import *`, banned, anchored to `alias` narrowed by `name` with value `"*"` (an `ImportFrom` narrowed by `names` cannot tell `*` from an explicit name) — to fix the record shape (`id`, `slug`, `category`, `anchor`, `status`, `rationale`, `principles`, `replacement`, examples) before any bulk authoring

## 3. Loader and validator

- [x] 3.1 Add `src/simplified_python/registry.py` with dataclasses for rule, principle, exclusion, and loaded registry, reading TOML via `tomllib`
- [x] 3.2 Implement strict record validation: reject missing required fields, unknown fields, and wrong field types, with every error naming the source file and rule identifier
- [x] 3.3 Implement anchor resolution: reject empty node lists, node names absent from the live `ast` module, and narrowing attributes that any listed node type does not define
- [x] 3.4 Implement status validation: `restricted` requires `condition`, `banned` requires `replacement`, `allowed` permits neither, any other status value is rejected with the three valid values listed
- [x] 3.5 Implement principle validation: `restricted` and `banned` rules must cite at least one principle, and every cited identifier must resolve
- [x] 3.6 Implement identifier validation: `SP` plus three digits, identifier and slug unique across files, identifier inside its category's block, retired identifiers never reassigned
- [x] 3.7 Implement grammar enumeration by recursive `ast.AST.__subclasses__()` walk, treating leaf classes as concrete constructs, and assert it yields 119 leaves on the target version
- [x] 3.8 Implement coverage validation: every non-excluded leaf classified by exactly one unnarrowed rule, failing with the full list of unclassified and of doubly-classified node names
- [x] 3.9 Implement exclusion validation: every exclusion has a reason and category, and no node is both excluded and classified
- [x] 3.10 Implement the interpreter gate: fail with a message naming the declared and running versions when they differ, and never skip silently
- [x] 3.11 Implement ledger validation in both directions: every ledger identifier resolves to exactly one active rule or one retired entry, and every active and retired identifier appears in the ledger
- [x] 3.12 Implement example validation: every example parses at the target version, every violating example contains its rule's anchored construct, a `banned` rule's compliant example does not, every rule has a compliant example, and every `restricted` or `banned` rule has a violating example
- [x] 3.13 Expose `validate()` that collects and returns **all** errors rather than raising on the first, so authoring is not a one-error-per-run loop
- [x] 3.14 Add `python -m simplified_python.registry --check` printing grouped errors and exiting non-zero on failure

## 4. Validator tests

- [x] 4.1 Add `tests/fixtures/` containing deliberately broken miniature registries, one per failure mode from tasks 3.2 through 3.12
- [x] 4.2 Add negative tests asserting each broken fixture fails with an error that names the offending file, rule, and field
- [x] 4.3 Add a coverage test over the real registry asserting zero unclassified and zero doubly-classified nodes
- [x] 4.4 Add example-fixture tests parametrised per rule, so one failing rule produces one failing test case
- [x] 4.5 Add tests for the interpreter gate, the ledger in both directions, and rejection of a retired identifier being reused

## 5. Author the rules

Each task below classifies every leaf node in its block, gives every `restricted` or `banned` rule a rationale, at least one principle citation, and compliant plus violating examples, and leaves `python -m simplified_python.registry --check` no worse than before.

- [x] 5.1 Resolve the open questions recorded in `design.md` (template strings, the decorator allowlist, whether `async` syntax is in scope yet, whether annotations can be required under the current anchor model) and record each verdict in the affected rules
- [x] 5.2 `expressions.toml` (SP1xx): names, constants, calls, attributes, subscripts and slices, operator groups, boolean and comparison operators, expression contexts, f-strings, template strings, `IfExp`, `Starred`, `Lambda`, comprehensions and the `comprehension` product type, and the walrus ban
- [x] 5.3 `statements.toml` (SP2xx): `Module`, `Expr`, `Assign`, `AnnAssign`, `AugAssign`, `Delete`, `Pass`, and the `Global` and `Nonlocal` bans
- [x] 5.4 `control-flow.toml` (SP3xx): `If`, `While`, `For`, `Break`, `Continue`, `With` and `withitem`, `Match` with every `Match*` node and `match_case`
- [x] 5.5 `functions.toml` (SP4xx): `FunctionDef`, `arguments`, `arg`, `keyword`, `Return`, `Yield`, `YieldFrom`, plus narrowed rules for the decorator allowlist, `*args`/`**kwargs`, and nested definitions
- [x] 5.6 `classes.toml` (SP5xx): `ClassDef` plus narrowed rules for class keywords (metaclasses), base lists, and decorators
- [x] 5.7 `imports.toml` (SP6xx): `Import`, `ImportFrom`, `alias`, the star-import ban from task 2.5, and a verdict on relative import depth
- [x] 5.8 `exceptions.toml` (SP7xx): `Try`, `TryStar`, `ExceptHandler`, `Raise`, `Assert`
- [x] 5.9 `async.toml` (SP8xx): `AsyncFunctionDef`, `AsyncFor`, `AsyncWith`, `Await`
- [x] 5.10 `typing.toml` (SP9xx): `TypeAlias`, `TypeVar`, `ParamSpec`, `TypeVarTuple`, and annotation-related narrowed rules
- [x] 5.11 Append every issued identifier to `subset/published-ids.toml` and set the initial `ruleset_version`
- [x] 5.12 Review the rule set as a whole for over-broad groups: confirm each grouped anchor shares one status and one rationale, and split any group that hides a distinct decision

## 6. Generated reference

- [x] 6.1 Add `src/simplified_python/reference.py` rendering `docs/subset.md`: generated-file banner naming the regeneration command and the registry, then the principles section, then the rule index, then the entries
- [x] 6.2 Render each entry with identifier, slug, status, the construct in plain language, rationale, principle citations as in-document links, and examples as fenced Python blocks copied verbatim; show `restricted` conditions, and place a `banned` rule's violating example next to its replacement
- [x] 6.3 Derive each entry's in-document anchor from the identifier alone, and render the index as a table of identifier, slug, and status linking to entries
- [x] 6.4 Make generation deterministic: categories in manifest order, rules by identifier, no dependence on filesystem iteration order
- [x] 6.5 Add `python -m simplified_python.reference` to write the document, refusing to write anything when validation fails
- [x] 6.6 Add tests: two runs are byte-identical, shuffled input file order changes nothing, and generation aborts on an invalid registry
- [x] 6.7 Add the staleness test that regenerates in memory and byte-compares the committed `docs/subset.md`, failing with instructions to regenerate
- [x] 6.8 Generate and commit `docs/subset.md`
- [x] 6.9 Generate a summary of banned and restricted rules into `README.md` between markers, linked to `docs/subset.md`, and cover it with the staleness check

## 7. Wiring and closeout

- [x] 7.1 Add a CI workflow pinned to Python 3.14 that runs registry validation, the test suite, and the staleness check
- [x] 7.2 Update `README.md` to state the subset-of-Python invariant and link to `docs/subset.md` as the reference, with no hand-written restatement of rules (the summary in task 6.9 is generated)
- [x] 7.3 Record in `AGENTS.md`: validate, generate, and test commands; the rule that the registry is edited and the document is never hand-edited; and how to add a rule
- [x] 7.4 Traceability pass: confirm every scenario in `specs/subset-rules/spec.md` and `specs/subset-reference/spec.md` maps to a test, and list any scenario that does not
  - Every scenario maps to a test in `tests/test_validator.py`, `tests/test_registry.py`, or `tests/test_reference.py`, with these exceptions:
  - *Rule exists only in the registry* and *Prose claim contradicts the registry* are normative policy, not testable behaviour. They are enforced by convention (`README.md` and `AGENTS.md` point to the registry and do not restate rules).
  - *Rule status changes* is covered only in part. `changelog-stale` checks that the latest changelog entry records the current `ruleset_version`. Without history, nothing can detect a status change that did not raise the version.
  - *New grammar node appears after an upgrade* is simulated by the `coverage-unclassified` fixture (`TemplateStr` and `Interpolation` without a rule), because a real upgrade cannot run in-process.
- [x] 7.5 Run `openspec validate define-python-subset --strict` and resolve anything it reports
