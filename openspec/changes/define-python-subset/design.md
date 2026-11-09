# Design: Defining the Simplified Python Subset

## Context

The repository is empty apart from a README, a licence, and a Python `.gitignore`. There is no prior code, no packaging, and no specs in `openspec/specs/`, so this change sets the conventions everything later inherits.

The primary consumer is the **human reviewer**. The subset exists to lower the cost of reading a diff, so the definition must answer "is this construct allowed?" the same way every time, for every reviewer, with the reasoning attached. A secondary consumer is the **checker** that a later change will build; it must be able to read the definition as data rather than re-encoding it from prose.

Two constraints shape the design:

1. **The subset only removes syntax.** A conforming file is a valid Python file with identical semantics. There is no transpiler, so the definition is a classification over Python's existing grammar, not a grammar of its own.
2. **Completeness must be provable, not asserted.** A style guide that covers "the constructs someone remembered" leaves reviewers arguing about the rest. CPython's `ast` module already enumerates the grammar, so the definition can be checked for total coverage mechanically.

Measured on the local interpreter (CPython 3.14.5): walking `ast.AST.__subclasses__()` recursively yields 132 classes, of which 119 are leaves; 10 of those leaves cannot appear in a tree from `ast.parse(mode="exec")`, leaving **109 constructs that must be classified**.

## Prior Art

**Closest production analog: [Starlark](https://starlark-lang.org/spec.html) (Bazel's configuration language, formerly Skylark).** Starlark is explicitly "a subset of Python," restricted for determinism and reviewability — no classes, no exceptions in the base language, no unbounded recursion, restricted mutation, order-independent evaluation. It validates the overall project shape: a Python-derived language can be narrowed for a reader's benefit and still ship at scale. It differs in one important respect — Starlark's completeness is a hand-written language specification, not a mechanically provable coverage claim against every AST node. The exhaustive-coverage guarantee in this design (Requirement: Exhaustive coverage of the target grammar) is more rigorous than the closest production precedent, not a redundant one.

**Rule-record format precedent: [SEI CERT coding standards](https://wiki.sei.cmu.edu/confluence/display/PY) and [SonarSource's rule repository](https://github.com/SonarSource/rspec).** CERT's C, C++, and Python standards use a stable rule ID, a rationale/discussion, and paired noncompliant/compliant examples — structurally close to this registry's `id`, `rationale`, and example fields. SonarSource's `rspec` repository is a structured rule-metadata source from which analyzer-facing documentation is generated, which is direct precedent for treating the registry as the source of truth and `docs/subset.md` as generated output. Neither achieves exhaustive coverage: both catalogue *known* problematic patterns rather than classifying every reachable grammar construct exactly once. CERT Python specifically is security-focused (injection, deserialization, unsafe resource handling) and is not a grammar-subset standard at all.

**Other restricted-Python precedents considered and set aside as weaker analogs:** [RestrictedPython](https://github.com/zopefoundation/RestrictedPython) (Zope) restricts via AST-transforming compiler guards for sandboxing, not for review — its concern is runtime safety, not reader cost, and it explicitly does not claim to be a complete security boundary on its own. [RPython](https://rpython.readthedocs.io/) (PyPy) restricts Python for static analyzability and translation, not human review. MicroPython and CircuitPython subtract features for hardware constraints, not reviewability. None of these publish a stable per-construct rule registry with rationale and examples.

**No comparable "Python subset for AI-generated code" standard was found.** Existing agent-oriented tooling (Google's style guide, agent framework documentation, sandboxed-execution projects such as SWE-agent) addresses this problem through sandboxing and repository-local instructions, not through a formal, exhaustively-classified subset language. Combined with the coverage guarantee above, this appears to be the project's genuinely novel contribution rather than a reimplementation of existing work.

## Goals / Non-Goals

**Goals:**

- A machine-readable registry that classifies every construct in the target grammar as `allowed`, `restricted`, or `banned`, with a rationale for each narrowing.
- Provable total coverage: adding a construct to Python breaks the build until someone decides about it.
- A generated human reference that cannot disagree with the registry, with stable per-rule links reviewers can cite in review comments.
- Self-verification before any checker exists: the registry's own examples are executed as fixtures.
- The least scaffolding that makes the above runnable.

**Non-Goals:**

- The checker, CLI, or CI gate that enforces the subset on real code. This change produces the definition it will read.
- Severity levels, warning tiers, or per-project rule configuration. Enforcement policy belongs to the checker; the definition states only what the subset is.
- Formatting and layout rules (line length, quote style, one statement per line). These are invisible to the AST and belong to a formatter change.
- Restrictions on library and builtin use (`eval`, dynamic `getattr`, monkey-patching, threading). These are name- and semantics-level rules, not grammar, and need a different anchoring mechanism.
- Code metrics — nesting depth, complexity, function length, parameter count. These are aggregate properties of a region measured against a number, which a construct anchor cannot express. They are defined as a distinct artifact kind by the `define-code-metrics` change, which shares this registry's principles, identifier ledger, and reference document without altering any requirement here.
- Agent-facing prompt guidance or rule autofixes.

## Decisions

### Rules are anchored to CPython AST node types

Each rule names one or more `ast` class names, optionally narrowed to one attribute of those nodes. A narrowed anchor may also give a `value`: the construct is then present only where the attribute equals it (`alias.name == "*"` is a star import); without a `value`, the construct is present wherever the attribute is non-empty (`ClassDef.keywords`, `ImportFrom.level`). Without `value`, `ImportFrom` narrowed by `names` would match every `from` import, and a banned rule's compliant example could never show the sanctioned form.

Anchoring to the AST is what makes coverage provable: CPython publishes the node set, so the registry can be diffed against it instead of against someone's memory. It also means the future checker's implementation and the definition share one vocabulary — a rule anchored to `NamedExpr` maps to a visitor for `NamedExpr` with nothing lost in translation. Anchors are also immune to reformatting, so a rule cannot be dodged by rearranging whitespace.

- *Rejected: prose-anchored rules.* Cannot be enumerated, so completeness is unknowable and the checker must re-interpret English.
- *Rejected: token or CST anchoring (for example libcst).* It would capture surface concerns the AST discards, but it adds a dependency, introduces a second grammar model to keep in step with the first, and offers no comparable enumeration of "all constructs". Surface concerns are deferred to a formatter instead.
- *Accepted cost:* the AST erases distinctions a reviewer may care about — parenthesisation, quote style, statements crammed onto one line. Those are explicitly out of scope, and the design records that boundary rather than papering over it.

### A rule may group several node types

`anchor.nodes` is a list. One rule covers `Add`, `Sub`, `Mult`, `Div`, `FloorDiv`, `Mod`, and `Pow`; coverage still requires that each node type be classified by exactly one unnarrowed rule.

The alternative — strict one rule per node type — would produce 109 rules, most of them saying "this obviously ordinary construct is allowed". That buries the twenty or so decisions that actually matter and makes the reference unreadable, defeating the point. Grouping should produce roughly 45 to 60 rules, with the interesting ones standing out.

*Accepted cost:* grouping is a judgement call, and a group that is too coarse can hide a decision (for instance grouping `Yield` with `YieldFrom` when they deserve separate verdicts). Mitigation: groups are limited to constructs that share both status and rationale, which is checkable in review because rationale is a required field.

### TOML as the registry format

Read with `tomllib` from the standard library.

- *Rejected: YAML.* Requires PyYAML, so every consumer of the definition inherits a dependency, and YAML's implicit typing is a poor fit for data that includes code snippets.
- *Rejected: JSON.* No comments, and code examples become unreadable escaped one-liners — hostile to the reviewers this project serves.
- *Rejected: a Python module of dicts.* Data that executes on import cannot be trusted or consumed by non-Python tooling, which is a poor look for a project about reviewability.

TOML's multi-line literal strings (`'''`) hold Python snippets verbatim, with no escaping, which matters because the snippets are executed as fixtures.

### Registry layout: a manifest plus one file per category

```
subset/
  registry.toml          # target version, rule-set version, ordered categories and id blocks
  principles.toml        # P1..Pn: the review costs that justify narrowing Python
  exclusions.toml        # node types that cannot appear, with a reason each
  published-ids.toml     # append-only ledger of every id ever issued
  rules/
    expressions.toml     # SP1xx
    statements.toml      # SP2xx
    control-flow.toml    # SP3xx
    functions.toml       # SP4xx
    classes.toml         # SP5xx
    imports.toml         # SP6xx
    exceptions.toml      # SP7xx
    async.toml           # SP8xx
    typing.toml          # SP9xx
```

One file per category keeps diffs local and gives each file a reviewable size. The manifest holds the numeric block per category so identifier allocation is checkable rather than conventional.

### Identifiers: a numeric code plus a slug

Every rule carries both `id = "SP142"` and `slug = "no-walrus"`. The code is canonical: machine output uses it, review comments cite it, and the reference's in-document anchors derive from it alone. The slug exists so humans can read the rule set.

- *Rejected: slug-only (ESLint style).* Renaming for clarity would break every existing citation, which discourages exactly the clarifying edits the project wants.
- *Rejected: code-only.* Opaque; nobody remembers what `SP142` forbids.

Deriving anchors from the code alone is what lets a slug be reworded without breaking links — this is the reason to accept the cost of two identifiers.

### Restricted conditions are prose plus an anchor, not an executable predicate

A `restricted` rule records a machine-readable anchor (nodes, optionally one attribute) and a **prose** `condition` such as "only one `for` clause" or "no `*` target". It does not record an executable predicate.

- *Rejected: a predicate DSL in TOML.* Inventing a small language means writing a parser, an evaluator, and error messages for it, and asking reviewers to learn it — a large cost for perhaps a dozen conditions.
- *Rejected: Python expressions in TOML evaluated at load time.* Registry data that executes arbitrary code, in a project whose purpose is reviewability, is indefensible.

*Accepted risk and its mitigation:* the checker will implement each condition in code, so a condition could drift from its prose. Every `restricted` rule therefore requires compliant and violating examples, and the checker change will be required to classify all registry examples correctly. Drift then surfaces as a failing test rather than as a disagreement in review.

### Coverage is computed from leaf classes, with justified exclusions

Validation walks `ast.AST.__subclasses__()` recursively and treats **leaf classes** as the concrete constructs. A class with subclasses is an ASDL sum type (`expr`, `stmt`, `operator`) and is abstract by construction, so abstractness is derived rather than hand-listed. ASDL product types (`arguments`, `arg`, `keyword`, `alias`, `withitem`, `comprehension`, `match_case`) are leaves, do appear in real trees, and must be classified — they carry real decisions, such as whether `*args` is permitted or whether `from x import *` is allowed.

The 10 leaves that cannot appear in an `exec`-mode tree go in `exclusions.toml`, each with a reason and one of three categories:

- *deprecated placeholder:* `AugLoad`, `AugStore`, `Param`, `Suite`, `Index`, `ExtSlice`
- *alternate parse root:* `Interactive`, `Expression`, `FunctionType`
- *opt-in parse flag:* `TypeIgnore` (only with `type_comments=True`)

Requiring a per-entry reason is what keeps the exclusion list from becoming a dumping ground for constructs nobody wanted to decide about.

### Target version 3.14, enforced by hard failure

`registry.toml` declares `python_version = "3.14"`. Validation that touches the live `ast` module fails loudly on any other interpreter.

3.14 is the local and CI toolchain version, and it is the version where the grammar includes template strings (`TemplateStr`, `Interpolation`) — a construct that deserves an explicit verdict rather than silent omission. Deprecated AST aliases are already gone, so the node set is clean.

- *Rejected: vendoring a snapshot of the node list so tests run on any interpreter.* The snapshot would be precisely the hand-maintained list that total coverage is designed to eliminate, and it would go stale silently. The whole value is that CPython tells us when the grammar grows.
- *Rejected: skipping coverage on a mismatched interpreter.* A silently skipped completeness check is worse than no check, because it reports success.

### The reference is generated and staleness is a test failure

`docs/subset.md` is written by `python -m simplified_python.reference`. A test regenerates into memory and compares bytes with the committed file, so an edit to the registry without regeneration fails CI, and a hand-edit of the document fails too. Generation is deterministic — categories in manifest order, rules by identifier — so the comparison is meaningful and diffs stay small.

- *Rejected: a hand-written reference with a linter that checks it mentions every rule.* Mentioning is not agreeing; the prose would still drift from the data.
- *Rejected: a generated static site.* Premature. Markdown in the repository is reviewable in a diff, which is the point.

### Minimal scaffolding: `src/` layout, pytest for tests only

`pyproject.toml` with a `src/simplified_python/` package holding `registry.py` (load and validate) and `reference.py` (generate). No runtime dependencies; pytest as the only development dependency.

pytest is chosen over stdlib `unittest` because the suite is table-driven over every rule — parametrisation gives one clear failure per offending rule instead of one failure for the whole table. The cost is a development dependency in a repository that otherwise has none; that is accepted because it never reaches consumers of the registry.

### Initial verdicts that set the tone

The machinery above is neutral, but a few verdicts define the project's character and should be settled during implementation rather than discovered rule by rule. The starting position:

| Construct | Status | Reasoning |
|---|---|---|
| `from x import *` | banned | A reader cannot tell where a name came from |
| Walrus `:=` | banned | Assignment hidden inside an expression |
| `global` / `nonlocal` | banned | Action at a distance |
| Metaclasses, `__init_subclass__` hooks via class keywords | banned | Class behaviour defined somewhere the reader is not looking |
| Decorators | restricted to a declared allowlist | Silently replaces the function being read |
| Comprehensions | restricted to one `for` and at most one `if` | Nested comprehensions are read inside-out |
| `lambda` | restricted to a single call argument | Named functions are greppable and testable |
| Nested function definitions | restricted | Closures hide captured state |
| `try` / `except*` | banned | Exception groups double the control-flow paths |
| Chained comparisons (`a < b < c`) | restricted | Readable at two operands, puzzling beyond |
| `match` | allowed | Explicit, exhaustive, flat — the kind of construct the subset wants |

These are the starting point for review, not a settled outcome; each needs its rationale and examples written before it counts.

## Risks / Trade-offs

- **The subset is only as good as its verdicts, and verdicts are opinions.** → Every non-`allowed` rule must cite a numbered principle, so disagreement happens over a principle once rather than over each rule forever. Principles are few and stated in the reference.
- **Rule identifiers become public API the moment anyone cites one.** → An append-only ledger of issued identifiers plus a retired list, both validated, make an accidental renumber a build failure.
- **Prose conditions on `restricted` rules can drift from the checker.** → Mandatory examples become the checker's acceptance tests in the next change.
- **Tying coverage to the live `ast` module couples the repository to one interpreter version.** → Accepted deliberately; the failure is loud and the fix is to classify the new constructs, which is the work we want to be forced to do. A version bump becomes a normal, visible change.
- **Grouped anchors can hide a decision inside a group.** → Groups must share status *and* rationale; the rationale field makes an over-broad group visible in review.
- **Over-restriction would make the subset unusable and quietly ignored.** → Restricting is preferred to banning where a condition can be stated, and the `restricted` status exists precisely so the answer is not always binary. Real-world validation (running the checker over an existing codebase) belongs to the checker change and will be the first honest test of calibration.
- **Ceremony cost: adding a rule touches a category file, the ledger, and the generated reference.** → The reference is regenerated by a command, so the manual cost is two files. If the ledger proves to be friction without benefit, it is cheap to drop later; dropping it is easier than reconstructing identifier history.

## Migration Plan

Not applicable: there is no existing code, no consumers, and nothing to roll back. The change is additive. The first genuine migration decision arrives when the target Python version is raised, and the mechanism for that is already specified — coverage validation fails until the new constructs are classified, and the rule-set version is raised alongside.

## Resolved Questions

The open questions were settled during implementation. Each verdict is recorded in the affected rules.

- **Template strings (`TemplateStr`, `Interpolation`, PEP 750): banned** (SP113). They give a second spelling close to f-strings, and their effect is decided by the code that consumes the template. Use an f-string and call any escaping function explicitly.
- **Decorator allowlist: the core standard-library set** (SP405, SP504). Function decorators: `@property`, `@<name>.setter` and `@<name>.deleter`, `@staticmethod`, `@classmethod`, `@override` / `@typing.override`. Class decorators: `@dataclass` / `@dataclasses.dataclass`, with or without keyword arguments. Framework decorators are not permitted. The allowlist is name-based, so the listed names must not be rebound.
- **`async` syntax: not yet in the subset** (SP801, SP802). Every async construct, including async comprehensions, is banned for this rule-set version. This is an explicit "not yet", not a permanent verdict.
- **Type annotations: allowed, not required** (SP903, SP904). A rule that requires annotations would be a rule about a construct that is absent, and the anchor model cannot express that. If required annotations are wanted later, the anchor model needs an addition in its own change.
- **Relative imports: at most one leading dot** (SP603).
- **Anchor value matching.** An `ImportFrom` anchor narrowed by `names` cannot tell `from x import *` from `from x import y`. Narrowed anchors therefore accept an optional `value` (see "Rules are anchored to CPython AST node types"), and the star-import ban anchors to `alias.name == "*"`.
