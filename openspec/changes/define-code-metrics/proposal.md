# Define Review-Cost Code Metrics

## Why

`define-python-subset` classifies every construct in the grammar, but classification cannot express the properties that make a reviewer give up: a function that nests six levels deep, spans 300 lines, or takes eleven parameters breaks no construct rule. Those costs are aggregate properties of a region of code measured against a number, not constructs that are present or absent, so they need a second kind of rule.

The gap is not hypothetical. The subset can ban every construct on its list and still permit a function no reviewer will read carefully. Metrics close that gap, and they answer to the same principle the construct rules already cite — bounded reading cost.

## What Changes

- **A metric catalogue as a distinct artifact.** `subset/metrics.toml`, with its own schema and its own `SM` identifier namespace, separate from the construct registry. Metrics are not rules, and keeping the terms distinct keeps both schemas simple and reviewable.
- **Five metrics for the first release.** Maximum nesting depth (the hard structural limit), cognitive complexity (the weighted aggregate), function line span, function statement count, and parameter count.
- **Nesting depth carries the structural limit, not cyclomatic complexity.** McCabe counts independent test paths, so a flat twelve-case `match` and twelve nested `if`s both score 13 — backwards for a project that treats flat, explicit branching as exemplary. Nesting depth is unambiguous, and unlike a length limit it cannot be satisfied without genuinely flattening logic.
- **Every metric ships an executable reference implementation.** A threshold without an exact counting rule is not a specification: `radon`, `mccabe`, ruff's `C901`, and Sonar return different numbers for the same function because they disagree about `and`/`or`, `elif`, `except` handlers, comprehension `if`s, and `match` cases. Each metric is therefore defined by a pure function of an AST region plus test vectors that pin the cases where tools disagree.
- **Two length metrics, deliberately.** Physical line span measures what a reviewer scrolls through; statement count is immune to reformatting. They measure different costs, so each gets its own threshold and rationale rather than one standing in for the other.
- **Thresholds are measured, not asserted.** Each threshold records its corpus, percentile, and measurement date. The corpus is the CPython standard library on the pinned interpreter — 655 files already on disk, reproducible with no network access.
- **No suppression affordance.** The catalogue defines no per-occurrence waiver. Thresholds are therefore calibrated high enough that only genuine outliers trip, and the escalation path for an outlier is to re-argue the threshold as a visible registry diff.

Explicitly **not** in this change: cyclomatic complexity thresholds, the checker that computes metrics over a real codebase, per-project configuration, waiver or suppression mechanisms, Halstead measures and maintainability indices, and coupling metrics such as fan-in and fan-out.

## Capabilities

### New Capabilities

- `code-metrics`: the metric catalogue — record schema, measurement region definitions, reference implementations, test vectors that pin counting rules, the five metrics and their thresholds, calibration provenance, the absence of a suppression affordance, and how metrics appear in the generated reference.

### Modified Capabilities

None. Metrics are a distinct artifact kind in a distinct file, so every requirement in `subset-rules` and `subset-reference` remains true as written: those specs govern *rules* under `subset/rules/` and the reference document's rule entries, neither of which this change alters. Construct coverage, identifier allocation, and the staleness guarantee are untouched.

## Impact

- **Depends on `define-python-subset` being implemented**, not merely proposed: this change adds to that registry's directory, reuses its principles file and identifier ledger, and extends its reference generator.
- **New files:** `subset/metrics.toml`, `subset/metric-vectors.toml`, `src/simplified_python/metrics.py`, plus a calibration script and tests.
- **Extended files:** `subset/published-ids.toml` gains the `SM` namespace; `src/simplified_python/reference.py` gains a metrics section; `docs/subset.md` is regenerated.
- **Toolchain:** unchanged. No runtime dependencies; the calibration corpus is the standard library of the pinned interpreter.
- **Downstream commitments:** `SM` identifiers become citable in review comments, so they are ledgered and never reused. The reference implementations become the normative definition of each metric — the checker must call them rather than reimplement them.
- **Honest limitation to record in the reference:** the metric set is curated and carries no completeness guarantee, unlike construct coverage, which is provable against CPython's grammar. Readers must not assume parity between the two.
