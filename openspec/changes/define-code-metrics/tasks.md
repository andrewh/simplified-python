# Tasks: Define Review-Cost Code Metrics

Depends on `define-python-subset` being implemented — this change extends its registry directory, principles, ledger, and reference generator. Calibration runs late, after the construct rules exist, so thresholds are not set against a distribution the subset makes unreachable.

## 1. Prerequisites and open verdicts

- [ ] 1.1 Confirm `define-python-subset` is implemented: registry validation passes, `docs/subset.md` is generated, and the identifier ledger exists
- [ ] 1.2 Decide whether a nested function's body counts toward its enclosing function's line span and statement count, and record the verdict with its reasoning
- [ ] 1.3 Decide whether parameter count distinguishes keyword-only from positional parameters, taking the construct rules on `*args` and `**kwargs` into account
- [ ] 1.4 Decide whether decorator lines fall inside a function's region, and record it as the region boundary rule
- [ ] 1.5 Confirm the region set for the first release is function-level only, and record class-level and module-level metrics as deferred

## 2. Catalogue and loader

- [ ] 2.1 Write `subset/metrics.toml` with the region definitions and five metric records (`SM01` nesting depth, `SM02` cognitive complexity, `SM03` line span, `SM04` statement count, `SM05` parameter count), leaving thresholds unset until task 5
- [ ] 2.2 Add `src/simplified_python/metrics.py` with dataclasses for a metric record and its calibration, loading `subset/metrics.toml` via `tomllib`
- [ ] 2.3 Implement strict record validation: required fields, unknown fields, wrong types, thresholds that are not positive integers, and empty principle lists, with every error naming the metric identifier and field
- [ ] 2.4 Implement region validation: every metric declares a region the catalogue defines, and `async def` resolves to the same region as `def`
- [ ] 2.5 Implement rejection of any suppression, severity, or advisory field, with an error stating that the catalogue defines no suppression affordance
- [ ] 2.6 Extend identifier validation to the `SM` namespace: `SM` plus two digits, unique against every construct identifier, present in the ledger, never reused
- [ ] 2.7 Extend the registry validation entry point and `--check` command to report metric errors alongside construct rule errors, still collecting all errors rather than raising on the first

## 3. Reference implementations

- [ ] 3.1 Implement the metric registry: a mapping from metric identifier to a pure function taking an AST region and returning a non-negative integer
- [ ] 3.2 Implement `SM01` maximum nesting depth, with `elif` chains and `match` cases not accruing depth beyond the statement that opens them
- [ ] 3.3 Implement `SM02` cognitive complexity: one increment per branch-introducing construct plus one per nesting level, boolean operator runs counted once, `else` free, `elif` adding one without deepening
- [ ] 3.4 Implement `SM03` line span from `lineno` and `end_lineno`, honouring the region boundary verdict from task 1.4
- [ ] 3.5 Implement `SM04` statement count and `SM05` parameter count, honouring the verdicts from tasks 1.2 and 1.3
- [ ] 3.6 Implement two-way binding validation: every metric has an implementation and every implementation is bound to a metric
- [ ] 3.7 Add tests asserting every implementation returns a non-negative integer and raises nothing across a sample of standard library functions

## 4. Test vectors

- [ ] 4.1 Create `subset/metric-vectors.toml` keyed by metric identifier, with a header comment stating that vectors are the normative counting rule
- [ ] 4.2 Write vectors for `SM01` and `SM02` covering every enumerated disagreement construct: `and`/`or` sequences, `elif` chains, `else`, `except` handlers, conditional expressions, comprehension `if` clauses, `match` cases, and nested definitions
- [ ] 4.3 Write vectors for `SM03`, `SM04`, and `SM05`, including a single statement spread over many lines and a reformatted call that changes line span without changing statement count
- [ ] 4.4 Implement vector validation that fails naming the metric, the vector, the expected value, and the computed value
- [ ] 4.5 Implement coverage validation over vectors: fail when a metric lacks a vector for one of the enumerated disagreement constructs
- [ ] 4.6 Add the discriminating tests from the specs: a twelve-case flat `match` scoring below a four-level nest, and a guard-clause rewrite falling below the nesting threshold

## 5. Calibration

- [ ] 5.1 Add a calibration script that walks the pinned interpreter's standard library, excluding test packages, and reports per-metric distributions with percentiles
- [ ] 5.2 Run the calibration and record the distributions, including how much of the corpus each candidate threshold would flag
- [ ] 5.3 Choose a percentile per metric — not one percentile globally — and record the reasoning, rejecting any threshold that would flag nothing in the corpus as decoration
- [ ] 5.4 Compare each chosen threshold against the corresponding existing default recorded in `design.md`'s Prior Art section (ruff `C901`/`PLR09xx`/`PLR1702`, flake8-cognitive-complexity, flake8-functions, NIST 500-235's risk bands) and record, per metric, whether the calibrated threshold lands near, above, or below the external default and why
- [ ] 5.5 Set the five thresholds and write each `calibration` record with corpus, percentile, and measurement date
- [ ] 5.6 Implement calibration validation: every threshold has a provenance record, and validation fails without one
- [ ] 5.7 Add a test that re-runs the calibration on the pinned interpreter and reproduces the recorded distribution without network access
- [ ] 5.8 Sanity-check the thresholds by hand against a handful of standard library functions a reviewer would agree are too complex, and record any threshold the numbers fail to justify

## 6. Reference integration

- [ ] 6.1 Extend `src/simplified_python/reference.py` with a metrics section rendering identifier, slug, region, threshold, counting rule, calibration provenance, and a worked example with its computed value
- [ ] 6.2 Derive metric anchors from the metric identifier alone, and add metrics to the document index alongside construct rules
- [ ] 6.3 Add the statement that the metric set is curated and carries no completeness guarantee, contrasted with provable construct coverage
- [ ] 6.4 Add the statement that cognitive complexity is defined locally and is not comparable with third-party tools
- [ ] 6.5 Confirm generation stays deterministic with metrics present: two runs byte-identical, input file order irrelevant
- [ ] 6.6 Regenerate and commit `docs/subset.md`, confirming the existing staleness check now covers the metrics section

## 7. Closeout

- [ ] 7.1 Confirm CI runs metric validation, vector validation, and the calibration reproduction test on the pinned interpreter
- [ ] 7.2 Append every `SM` identifier to `subset/published-ids.toml` and raise the rule-set version
- [ ] 7.3 Record in `AGENTS.md` how to add a metric: catalogue record, reference implementation, vectors, calibration, regenerate
- [ ] 7.4 Traceability pass: confirm every scenario in `specs/code-metrics/spec.md` maps to a test, and list any that does not
- [ ] 7.5 Run `openspec validate define-code-metrics --strict` and resolve anything it reports
