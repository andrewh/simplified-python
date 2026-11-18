# Proposal: review-cost code metrics

> **Status: proposed, not implemented.** Nothing in this document exists in the code yet.

## Why

The [subset definition](../design/subset.md) classifies every construct in the grammar, but classification cannot express the properties that make a reviewer give up: a function that nests six levels deep, spans 300 lines, or takes eleven parameters breaks no construct rule. Those costs are aggregate properties of a region of code measured against a number, not constructs that are present or absent, so they need a second kind of rule.

The gap is not hypothetical. The subset can ban every construct on its list and still permit a function no reviewer will read carefully. Metrics close that gap, and they answer to the same principle the construct rules already cite — bounded reading cost.

## What changes

- **A metric catalogue as a distinct artifact.** `subset/metrics.toml`, with its own schema and its own `SM` identifier namespace, separate from the construct registry. Metrics are not rules, and keeping the terms distinct keeps both schemas simple and reviewable.
- **Five metrics for the first release.** Maximum nesting depth (the hard structural limit), cognitive complexity (the weighted aggregate), function line span, function statement count, and parameter count.
- **Nesting depth carries the structural limit, not cyclomatic complexity.** McCabe counts independent test paths, so a flat twelve-case `match` and twelve nested `if`s both score 13 — backwards for a project that treats flat, explicit branching as exemplary. Nesting depth is unambiguous, and unlike a length limit it cannot be satisfied without genuinely flattening logic.
- **Every metric ships an executable reference implementation.** A threshold without an exact counting rule is not a specification: `radon`, `mccabe`, ruff's `C901`, and Sonar return different numbers for the same function because they disagree about `and`/`or`, `elif`, `except` handlers, comprehension `if`s, and `match` cases. Each metric is therefore defined by a pure function of an AST region plus test vectors that pin the cases where tools disagree.
- **Two length metrics, deliberately.** Physical line span measures what a reviewer scrolls through; statement count is immune to reformatting. They measure different costs, so each gets its own threshold and rationale rather than one standing in for the other.
- **Thresholds are measured, not asserted.** Each threshold records its corpus, percentile, and measurement date. The corpus is the CPython standard library on the pinned interpreter — 655 files already on disk, reproducible with no network access.
- **No suppression affordance.** The catalogue defines no per-occurrence waiver. Thresholds are therefore calibrated high enough that only genuine outliers trip, and the escalation path for an outlier is to re-argue the threshold as a visible registry diff.

Explicitly **not** in this proposal: cyclomatic complexity thresholds, the checker that computes metrics over a real codebase, per-project configuration, waiver or suppression mechanisms, Halstead measures and maintainability indices, and coupling metrics such as fan-in and fan-out.

## Impact

- **Builds on the implemented subset registry:** the metrics add to that registry's directory, reuse its principles file and identifier ledger, and extend its reference generator.
- **New files:** `subset/metrics.toml`, `subset/metric-vectors.toml`, `src/simplified_python/metrics.py`, plus a calibration script and tests.
- **Extended files:** `subset/published-ids.toml` gains the `SM` namespace; `src/simplified_python/reference.py` gains a metrics section; `docs/subset.md` is regenerated.
- **Toolchain:** unchanged. No runtime dependencies; the calibration corpus is the standard library of the pinned interpreter.
- **Downstream commitments:** `SM` identifiers become citable in review comments, so they are ledgered and never reused. The reference implementations become the normative definition of each metric — the checker must call them rather than reimplement them.
- **Honest limitation to record in the reference:** the metric set is curated and carries no completeness guarantee, unlike construct coverage, which is provable against CPython's grammar. Readers must not assume parity between the two.

## Context

The subset definition establishes a registry that classifies all 109 concrete constructs of the CPython 3.14 grammar as `allowed`, `restricted`, or `banned`, with total coverage provable against the `ast` module. That model has a known blind spot, recorded as an open question in its design: it can only match constructs that *appear*. It cannot express a property of a region measured against a number, so it cannot say anything about a function that nests six levels deep or runs for 300 lines.

Metrics fill that gap and answer to the same principle the construct rules cite — bounded reading cost. They are, however, a different kind of object, and three differences drive this design:

1. **No provable completeness.** CPython enumerates the grammar, so construct coverage can be checked. There is no enumerable universe of metrics, so the set is curated and the reference must say so rather than implying parity.
2. **No agreed definitions.** `radon`, `mccabe`, ruff's `C901`, and Sonar disagree about `and`/`or`, `elif`, `except`, comprehension `if`s, and `match` cases, so they return different numbers for the same function. A threshold is only meaningful alongside an exact counting rule.
3. **Thresholds are empirical.** A number chosen by folklore is exactly the arbitrary taste the principles were introduced to eliminate.

The measurement corpus is settled by convenience of the best kind: the CPython standard library on the pinned interpreter provides 655 candidate files already on disk, with no network access and no vendoring.

## Prior Art

**Existing default thresholds to calibrate against, not in isolation.** Several widely deployed tools already gate on metrics this catalogue defines, and their defaults are a sanity check for task 5.3's calibration rather than a substitute for it:

| Metric | Tool | Documented default |
|---|---|---|
| Cyclomatic complexity | flake8 `C901` / [ruff `C901`](https://docs.astral.sh/ruff/rules/complex-structure/) | 10 |
| Too many branches | [ruff `PLR0912`](https://docs.astral.sh/ruff/rules/#pylint-pl) | 12 |
| Too many arguments | ruff `PLR0913` | 5 |
| Too many statements | ruff `PLR0915` | 50 |
| Too many nested blocks | ruff `PLR1702` | 5 |
| Too many return statements | ruff `PLR0911` | 6 |
| Cognitive complexity | [flake8-cognitive-complexity](https://github.com/Melevir/flake8-cognitive-complexity) | 7 |
| Function length / params / branches | [flake8-functions](https://github.com/best-doctor/flake8-functions) | ~50 lines, 5 params, 12 branches |
| Cyclomatic complexity risk bands | [NIST SP 500-235](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication500-235.pdf) | 1–10 simple, 11–20 moderate, 21–50 high, 50+ untestable |

Notably, `PLR1702` already gates nesting depth with a default of 5 — task 5 should diff `SM01`'s counting rule against it explicitly (does `elif` add depth? does `match`?) rather than treat nesting depth as an unprecedented measure. [Radon](https://radon.readthedocs.io/) supplies the underlying cyclomatic-complexity computation for both `xenon` and `wily`, using letter grades `A` (1–5) through `F` (41+); `xenon`'s CI defaults require grade `A` project-wide, which is a considerably stricter posture than "generous, corpus-calibrated" thresholds and is not adopted here.

**Cognitive complexity is a deliberate citation, not a reimplementation.** `SM02`'s counting rules — increment per branch, additional increment per nesting level, a run of the same boolean operator counted once, `else` free — are drawn from [SonarSource's Cognitive Complexity whitepaper (Campbell, 2017)](https://www.sonarsource.com/docs/CognitiveComplexity.pdf). Sonar's own implementation is documented to vary by language, and `flake8-cognitive-complexity`'s counting behavior is independently plugin-specific, so no third-party implementation is authoritative enough to claim numerical equivalence with. `SM02`'s reference implementation and test vectors (Requirement: Counting rules are pinned by test vectors) are what make this project's definition exact; the whitepaper is cited for the principle, not treated as a specification this project implements.

**The no-suppression policy is a deliberate departure from every precedent found, not an oversight.** MISRA permits documented deviations, CERT documents exceptions, ESLint has `eslint-disable`, SonarQube has issue suppression, and Ruff has `# noqa` — every rule-based standard surveyed ships an escape hatch. This catalogue's Requirement: Catalogue defines no suppression affordance is therefore not "the industry norm"; it is a considered bet that a generous, corpus-calibrated threshold with zero escape hatch keeps every violation meaningful, at the cost of occasionally forcing a threshold renegotiation instead of a one-line waiver. Calibration (section 5 of the implementation plan below) is what has to carry that bet — if thresholds are set too tight, the absence of an escape hatch will surface as real friction rather than as a theoretical risk.

**No published methodology fixes "the" correct percentile.** NIST's risk bands are guidance, not a calibration procedure, and Code Complete's routine-size heuristics are heuristic rather than a reproducible statistical method. The corpus-percentile-and-date approach in Requirement: Thresholds record their calibration is a defensible engineering method but not one this project can cite as externally validated; task 5.3's per-metric percentile choice should be treated as this project's own judgment call, recorded so it can be argued with, not as the application of an established standard.

## Goals / Non-Goals

**Goals:**

- Five metrics that map to distinct review costs, each with a threshold a reviewer can cite.
- Every metric defined by an executable reference implementation, with test vectors pinning the cases where established tools disagree.
- Thresholds derived from a measured distribution, with corpus, percentile, and date recorded so the number can be argued with.
- Metrics rendered into the same reference document as construct rules, sharing its staleness guarantee and citation affordance.

**Non-Goals:**

- Cyclomatic complexity as a gate (see the decision below). It may later be reported without a threshold; that is not part of this proposal.
- The checker that computes metrics over a real codebase. This proposal defines the measures it will call.
- Waivers, suppression comments, severities, advisory tiers, or per-project configuration.
- Halstead measures, maintainability indices, and coupling metrics such as fan-in and fan-out — these measure properties of a system, not the reading cost of a diff.
- Class-level and module-level metrics in the first release (see Open Questions).

## Decisions

### A separate catalogue with its own `SM` namespace

Metrics live in `subset/metrics.toml` with their own schema and identifiers of the form `SM01`. They are called metrics, never rules.

The distinct term is what keeps the construct registry and its reference unchanged: they govern rules under `subset/rules/` and the reference's rule entries, so nothing about them has to be renegotiated. The distinct prefix means a citation carries its kind — `SM01` in a review comment is visibly a threshold rather than a construct verdict.

- *Rejected: a `kind` discriminator inside the construct rule schema.* A discriminated union in TOML means fields that are required for one kind and forbidden for another, which is precisely the sort of conditional data structure that is hard to review — self-defeating in this project.
- *Rejected: sharing the `SP` namespace via a reserved `SP0xx` block.* Workable, but it requires editing the other change's manifest and hides the kind at the point of citation.

*Shared deliberately:* the principles file, the identifier ledger, the reference document, and the validation entry point. Those are the things a reviewer experiences as one system.

### Nesting depth carries the hard limit; cyclomatic complexity carries none

McCabe complexity is decision points plus one, so a flat twelve-case `match` scores 13 and twelve nested `if` statements also score 13. For a project whose construct rules mark flat `match` as exemplary, a metric that cannot tell those apart is measuring the wrong thing: it measures the number of independent test paths, which is a testing concern, not reading cost.

Nesting depth is chosen for the hard limit because it is unambiguous to compute and, unlike every other metric here, it **cannot be satisfied by relocation**. A length or complexity limit can be met by extracting code into helpers; nesting depth can only be met by flattening — guard clauses, early returns, inverted conditions. The metric therefore pushes toward the specific rewrite that genuinely helps a reviewer.

Cognitive complexity is the aggregate companion: it charges for each branch and charges more when that branch sits inside other branches, which is the shape of the cost nesting depth measures only at its peak.

- *Rejected: McCabe with a threshold.* Penalises the flat branching the subset encourages.
- *Deferred, not rejected: McCabe reported without a threshold.* Useful for comparison with other tools, but a reported number with no consequence is decoration until someone asks for it.

### Cognitive complexity is defined locally, not borrowed

The measure increments once per branch-introducing construct and adds one further increment per level of nesting. A run of the same boolean operator counts once, `else` is free, and `elif` adds one increment without deepening.

This is inspired by SonarSource's cognitive complexity, but the catalogue will **not** claim equivalence. Their specification is prose plus a proprietary implementation; asserting parity we do not test would be exactly the kind of unverified claim this repository is built to avoid. The implementation and its vectors are the definition, and the reference says values are not comparable across tools.

### Two length metrics, because there are two costs

Physical line span (`end_lineno - lineno + 1`) measures what a reviewer scrolls through. Statement count measures structural size and is immune to reformatting. A single statement spread over 40 lines costs 40 lines of scrolling and is one statement; both facts are true, and collapsing them into one number would misrepresent one of them.

The cost of two metrics is two thresholds to calibrate and the risk of a reviewer wondering which one matters. Mitigation: each rationale names the cost it measures, and both values are always reported together. The alternative — one metric — would have required choosing between honesty about formatting and honesty about scrolling.

*Note a tension worth stating:* line span depends on formatting, which the subset definition deliberately placed out of scope for its AST-anchored rules. Line span is the one measure here that a formatter can move without changing code. It is included anyway because scrolling distance is a real cost, and the statement count metric exists precisely so that the format-independent view is also available.

### Reference implementations are the normative definition

`src/simplified_python/metrics.py` holds pure functions from an AST region to a non-negative integer, registered in a mapping keyed by metric identifier. Validation checks the mapping in both directions so a metric cannot exist without an implementation, nor an implementation without a threshold.

Binding the definition to code is what makes the counting rule exact. The prose `counting_rule` field remains, because a reviewer needs to read the intent, but where prose and implementation disagree the vectors decide — and a vector failure is a build failure.

### Vectors live in their own file

`subset/metric-vectors.toml`, keyed by metric identifier. Vectors are test data that will grow to perhaps twenty snippets per metric; inlining them would bury the eight fields a reviewer actually reads in the catalogue.

- *Rejected: vectors inline in the metric record.* Keeps the counting rule next to its examples, which is genuinely nicer at three vectors and unreadable at twenty.

The catalogue keeps one short worked example per metric for the reference document; the exhaustive vectors are test data.

### Calibration corpus: the standard library of the pinned interpreter

655 files, already on disk, fixed by the interpreter version, no network. Re-running the calibration on the pinned interpreter reproduces the distribution exactly, which is what makes the recorded provenance meaningful.

- *Rejected: a set of well-regarded third-party repositories.* Better stylistic role models, but they require vendoring or network access and they drift, which would make "the percentile we measured" unreproducible.

*Accepted limitation, stated plainly:* the standard library is not subset-conformant, contains decades-old code, and includes modules written under constraints that no longer apply. Calibrating against it risks importing its habits. It is therefore used as a **distribution reference** — to learn what values are ordinary and which are outliers — and not as a target. The honest follow-up is to re-calibrate once a meaningful body of subset-conformant code exists, and the recorded date exists so that re-calibration is visible.

### Thresholds are generous by construction

Because the catalogue defines no suppression affordance, a threshold set at the median would force contorted code with no escape. Thresholds are therefore set high enough that only genuine outliers trip — the calibration task reports the distribution and each threshold records the percentile it was set at.

This is a deliberate trade of strength for honesty. A tight threshold with a waiver mechanism becomes a rubber stamp; a generous threshold with no waiver keeps every violation meaningful. The follow-on risk is a threshold so generous it never fires, which the calibration report makes visible: if no file in the corpus would trip a threshold, it is decoration.

## Risks / Trade-offs

- **Every metric except nesting depth is gameable by extraction.** Ten fifteen-line functions that each call the next are worse to review than one linear 150-line function. → Thresholds are framed as tripwires that force a conversation, not as correctness properties, and the reference says so. Nesting depth is the limit that resists this, which is why it carries the hard gate.
- **Generous thresholds may never fire.** → The calibration report states, per metric, how much of the corpus would trip it. A threshold that flags nothing is reported as such and re-argued.
- **Calibrating on the standard library imports the standard library's habits.** → Used as a distribution reference only; the provenance record carries a date so staleness is visible, and re-calibration against subset-conformant code is the recorded follow-up.
- **A locally defined cognitive complexity is not comparable to any other tool's.** → The reference states this explicitly; the vectors are the specification; no parity is claimed.
- **Two length metrics can look like indecision.** → Each states the cost it measures, and both are always reported. A reviewer is never asked to pick.
- **The metric set is curated, so it has no completeness guarantee.** → Stated in the metrics section of the reference, directly contrasted with provable construct coverage, so readers do not transfer confidence from one to the other.
- **Region boundaries are where reproducibility usually breaks.** Whether a nested function's body counts toward its enclosing function changes values substantially. → Region definitions are a specified requirement with their own scenarios, and every metric declares its region.

## Migration Plan

This proposal is additive and builds on the implemented subset registry. Sequencing matters in one respect: thresholds should be calibrated **after** the construct rules are authored, because bans on nested definitions and limits on comprehensions already remove some of the complexity a metric would otherwise catch. Calibrating first would set thresholds against a distribution the subset itself makes unreachable.

Rollback is a file deletion plus a regeneration of the reference; no construct rule or identifier depends on a metric.

## Open Questions

- **What percentile?** p95 and p99 imply very different regimes — p99 on the standard library may be so permissive that nothing in normal code ever trips. The calibration report should be produced before this is settled, per metric rather than globally.
- **Does a nested function's body count toward its enclosing function's span and statement count?** It interacts directly with the subset's restriction on nested definitions (SP408), and the answer changes both length metrics materially. Needs a verdict before the implementations are written.
- **Are class-level and module-level metrics wanted?** Method count per class and statement count per module are the obvious candidates, and module length in particular is a real review cost. Deferred to keep the first release to regions with one unambiguous definition.
- **Should parameter count distinguish keyword-only parameters?** A function with eight keyword-only parameters reads very differently from one with eight positional ones, and the subset already restricts `*args` and `**kwargs` (SP406, SP407) in a way that changes the calculus.
- **Is line span measured before or after formatting?** The repository has no formatter and no line-length rule, so line span is currently measured on whatever the author wrote. If a formatter arrives later, this threshold's calibration is invalidated.

## Requirements

### Requirement: Metric catalogue is a distinct artifact
Metrics SHALL be defined in `subset/metrics.toml`, separate from the construct rules under `subset/rules/`, and SHALL be referred to as metrics rather than rules throughout the registry, the reference, and tool output. Metric identifiers SHALL use the prefix `SM` followed by two digits, so a citation reveals whether it names a construct verdict or a threshold. Metric identifiers SHALL be recorded in the same identifier ledger as construct rules and SHALL never be reused.

#### Scenario: Reviewer cites a threshold
- **WHEN** a reviewer cites `SM01` in a review comment
- **THEN** the identifier names a metric, and no construct rule can hold that identifier

#### Scenario: Metric is added to the ledger
- **WHEN** a new metric is defined
- **THEN** its identifier is appended to the identifier ledger and validation fails if it is absent

#### Scenario: Construct registry is unaffected
- **WHEN** the metric catalogue is loaded
- **THEN** construct coverage, construct rule schema validation, and construct identifier allocation behave exactly as before

### Requirement: Metric record schema
Every metric record SHALL declare `id`, `slug`, `region`, `threshold`, `counting_rule`, `rationale`, `principles`, and `calibration`. The loader SHALL reject a record that omits a required field, declares an unknown field, supplies a field of the wrong type, or supplies a threshold that is not a positive integer, and the error MUST name the offending metric identifier and field.

#### Scenario: Required field is missing
- **WHEN** a metric record omits `calibration`
- **THEN** loading fails with an error naming the metric identifier and the missing field

#### Scenario: Threshold is not a positive integer
- **WHEN** a metric declares a threshold of `0`, `-1`, or `7.5`
- **THEN** loading fails with an error naming the metric identifier

#### Scenario: Unrecognised field is present
- **WHEN** a metric record declares a field that is not part of the schema
- **THEN** loading fails rather than ignoring the field silently

#### Scenario: Metric cites no principle
- **WHEN** a metric record declares an empty `principles` list
- **THEN** loading fails, because every threshold must answer to a stated review cost

### Requirement: Measurement regions are precisely defined
Every metric SHALL declare the region it measures, and the catalogue SHALL define each region's boundaries unambiguously: which node types open a region, whether decorators are included, and how a nested region contributes to the region enclosing it. `async def` SHALL be measured identically to `def`. Validation SHALL reject a metric declaring a region the catalogue does not define.

#### Scenario: Nested region is measured
- **WHEN** a function contains a nested function definition
- **THEN** the nested body's contribution to the enclosing region is determined by the catalogue's stated rule, and the same answer is produced on every run

#### Scenario: Asynchronous function is measured
- **WHEN** a metric is computed for an `async def` and for the equivalent `def`
- **THEN** both produce the same value

#### Scenario: Decorators and the region boundary
- **WHEN** a decorated function is measured
- **THEN** whether the decorator lines fall inside the region follows the catalogue's stated boundary rule

#### Scenario: Metric names an undefined region
- **WHEN** a metric declares a region the catalogue does not define
- **THEN** loading fails with an error naming the metric and the unknown region

### Requirement: Every metric has an executable reference implementation
Each metric SHALL be bound to a pure function that takes an AST region and returns a non-negative integer, and that function SHALL be the normative definition of the metric. Validation SHALL check the binding in both directions and fail when a metric has no implementation or an implementation is bound to no metric.

#### Scenario: Metric has no implementation
- **WHEN** a metric is declared with no bound function
- **THEN** validation fails with an error naming the metric identifier

#### Scenario: Implementation is orphaned
- **WHEN** an implementation exists that no metric declares
- **THEN** validation fails, because an unreferenced measure has no definition or threshold

#### Scenario: Implementation returns an integer
- **WHEN** a metric's implementation is applied to any region of its declared kind
- **THEN** it returns a non-negative integer and does not raise

#### Scenario: Consumer computes a metric
- **WHEN** a downstream tool needs a metric value
- **THEN** it calls the bound reference implementation rather than reimplementing the counting rule

### Requirement: Counting rules are pinned by test vectors
Each metric SHALL carry test vectors mapping a code snippet to its expected value, and those vectors SHALL cover every construct on which established tools disagree: `and` and `or` sequences, `elif` chains, `else` branches, `except` handlers, conditional expressions, comprehension `if` clauses, `match` cases, and nested definitions. Validation SHALL run every vector and fail on any mismatch, naming the metric, the vector, the expected value, and the computed value.

#### Scenario: Implementation drifts from its counting rule
- **WHEN** an implementation is changed so that a vector no longer matches
- **THEN** validation fails, naming the metric, the vector, the expected value, and the computed value

#### Scenario: Disagreement construct has no vector
- **WHEN** a metric has no vector covering one of the enumerated disagreement constructs
- **THEN** validation fails with an error naming the metric and the uncovered construct

#### Scenario: Counting rule is revised
- **WHEN** a metric's counting rule is changed
- **THEN** the change is only accepted with vectors that demonstrate the new behaviour

### Requirement: Nesting depth is the hard structural limit
The catalogue SHALL define maximum nesting depth as the deepest chain of nested block-introducing statements within a region, and SHALL apply it as a hard threshold. An `elif` chain SHALL NOT accrue depth beyond the `if` that opens it, and `match` cases SHALL NOT accrue depth beyond the `match` that opens them, so flattening logic is the only way to satisfy the limit.

#### Scenario: Guard clauses replace nesting
- **WHEN** a function nested four levels deep is rewritten with early returns
- **THEN** its nesting depth falls and the rewritten form passes the threshold

#### Scenario: Flat branch chain is not penalised
- **WHEN** a function contains a twelve-case `match` with no nested blocks
- **THEN** its nesting depth is one level, not twelve

#### Scenario: Extraction does not disguise depth
- **WHEN** deeply nested logic is moved into a helper function that is itself deeply nested
- **THEN** the helper is measured as its own region and trips the same threshold

### Requirement: Cognitive complexity is the weighted aggregate
The catalogue SHALL define cognitive complexity as an increment per branch-introducing construct plus an additional increment for each level of nesting at which that construct appears, so nested branching costs more than flat branching. A sequence of the same boolean operator SHALL count once rather than once per operator, `else` SHALL add nothing, and `elif` SHALL add one increment without increasing the nesting level. The catalogue SHALL state that this is the project's own measure, defined by its implementation and vectors, and SHALL NOT claim equivalence with any third-party tool.

#### Scenario: Nesting outweighs breadth
- **WHEN** a twelve-case flat `match` and a four-level nest of `if` statements are both measured
- **THEN** the nested function scores higher than the flat one

#### Scenario: Boolean sequence counts once
- **WHEN** a condition is `a and b and c`
- **THEN** cognitive complexity increases by one for the sequence, not once per operator

#### Scenario: Equivalence is not claimed
- **WHEN** a reader compares a value with a third-party tool's output
- **THEN** the reference states that this measure is defined locally and that values are not comparable across tools

### Requirement: Length is measured by two distinct metrics
The catalogue SHALL define physical line span and statement count as separate metrics with separate thresholds, and each SHALL state in its rationale which cost it measures — scrolling distance for line span, and structural size independent of formatting for statement count. Neither SHALL be described as a proxy for the other.

#### Scenario: Reformatting moves one metric only
- **WHEN** a call is reformatted across more lines without changing its structure
- **THEN** line span increases and statement count is unchanged

#### Scenario: A single long expression
- **WHEN** a function consists of one statement spread over many lines
- **THEN** it can exceed the line span threshold while satisfying the statement count threshold

#### Scenario: Both values are reported
- **WHEN** a region is measured
- **THEN** both length metrics are reported, each against its own threshold

### Requirement: Thresholds record their calibration
Every threshold SHALL record the corpus it was measured against, the percentile it was set at, and the date of measurement. The corpus SHALL be reproducible without network access. Validation SHALL fail when a threshold has no calibration record, and changing a threshold SHALL require updating that record.

#### Scenario: Threshold has no provenance
- **WHEN** a metric declares a threshold with no corpus, percentile, or date
- **THEN** validation fails with an error naming the metric

#### Scenario: Calibration is reproduced
- **WHEN** the calibration is re-run against the recorded corpus on the pinned interpreter
- **THEN** the recorded distribution is reproduced without network access

#### Scenario: Threshold is changed
- **WHEN** a threshold is raised or lowered
- **THEN** the calibration record is updated in the same change and validation fails if it is not

#### Scenario: Reader questions a number
- **WHEN** a reader asks why a threshold is the value it is
- **THEN** the reference states the corpus, the percentile, and the date, so the number can be argued with rather than guessed at

### Requirement: Catalogue defines no suppression affordance
The metric catalogue SHALL NOT define any per-occurrence waiver, suppression comment, severity, or advisory status. Validation SHALL reject a metric record declaring such a field. Because no suppression exists, thresholds SHALL be set where genuine code passes, and the recorded route for an outlier is to re-argue the threshold as a change to the catalogue.

#### Scenario: Record declares a suppression field
- **WHEN** a metric record declares a suppression, severity, or advisory field
- **THEN** loading fails with an error stating that the catalogue defines no suppression affordance

#### Scenario: Legitimate outlier is encountered
- **WHEN** code exceeds a threshold for a defensible reason
- **THEN** the recorded route is a reviewed change to the threshold and its calibration, not a local waiver

### Requirement: Metrics appear in the generated reference
The generated reference SHALL contain a metrics section listing every metric with its identifier, slug, region, threshold, counting rule, calibration provenance, and a worked example showing a measured value. Each metric SHALL have a stable in-document anchor derived from its identifier, and metrics SHALL appear in the document index alongside construct rules. The section SHALL state that the metric set is curated and carries no completeness guarantee, in contrast to construct coverage.

#### Scenario: Reader looks up a threshold
- **WHEN** a reader opens a metric's entry
- **THEN** the entry shows the threshold, the counting rule, the calibration provenance, and a worked example with its computed value

#### Scenario: Reviewer cites a metric by link
- **WHEN** a reviewer links to a metric's anchor
- **THEN** the link resolves to that metric's entry and remains valid when the rationale or examples change

#### Scenario: Completeness is not overclaimed
- **WHEN** a reader reaches the metrics section
- **THEN** it states that metrics are curated, whereas construct coverage is provable against the grammar

#### Scenario: Catalogue changes without regeneration
- **WHEN** a metric is edited and the reference is not regenerated
- **THEN** the existing staleness check fails and instructs the author to regenerate

## Implementation plan

Builds on the implemented subset registry: it extends the registry directory, principles, ledger, and reference generator. Calibration runs late, after the construct rules exist, so thresholds are not set against a distribution the subset makes unreachable.

### 1. Prerequisites and open verdicts

- [x] 1.1 Confirm the subset registry is implemented: registry validation passes, `docs/subset.md` is generated, and the identifier ledger exists
- [ ] 1.2 Decide whether a nested function's body counts toward its enclosing function's line span and statement count, and record the verdict with its reasoning
- [ ] 1.3 Decide whether parameter count distinguishes keyword-only from positional parameters, taking the construct rules on `*args` and `**kwargs` into account
- [ ] 1.4 Decide whether decorator lines fall inside a function's region, and record it as the region boundary rule
- [ ] 1.5 Confirm the region set for the first release is function-level only, and record class-level and module-level metrics as deferred

### 2. Catalogue and loader

- [ ] 2.1 Write `subset/metrics.toml` with the region definitions and five metric records (`SM01` nesting depth, `SM02` cognitive complexity, `SM03` line span, `SM04` statement count, `SM05` parameter count), leaving thresholds unset until task 5
- [ ] 2.2 Add `src/simplified_python/metrics.py` with dataclasses for a metric record and its calibration, loading `subset/metrics.toml` via `tomllib`
- [ ] 2.3 Implement strict record validation: required fields, unknown fields, wrong types, thresholds that are not positive integers, and empty principle lists, with every error naming the metric identifier and field
- [ ] 2.4 Implement region validation: every metric declares a region the catalogue defines, and `async def` resolves to the same region as `def`
- [ ] 2.5 Implement rejection of any suppression, severity, or advisory field, with an error stating that the catalogue defines no suppression affordance
- [ ] 2.6 Extend identifier validation to the `SM` namespace: `SM` plus two digits, unique against every construct identifier, present in the ledger, never reused
- [ ] 2.7 Extend the registry validation entry point and `--check` command to report metric errors alongside construct rule errors, still collecting all errors rather than raising on the first

### 3. Reference implementations

- [ ] 3.1 Implement the metric registry: a mapping from metric identifier to a pure function taking an AST region and returning a non-negative integer
- [ ] 3.2 Implement `SM01` maximum nesting depth, with `elif` chains and `match` cases not accruing depth beyond the statement that opens them
- [ ] 3.3 Implement `SM02` cognitive complexity: one increment per branch-introducing construct plus one per nesting level, boolean operator runs counted once, `else` free, `elif` adding one without deepening
- [ ] 3.4 Implement `SM03` line span from `lineno` and `end_lineno`, honouring the region boundary verdict from task 1.4
- [ ] 3.5 Implement `SM04` statement count and `SM05` parameter count, honouring the verdicts from tasks 1.2 and 1.3
- [ ] 3.6 Implement two-way binding validation: every metric has an implementation and every implementation is bound to a metric
- [ ] 3.7 Add tests asserting every implementation returns a non-negative integer and raises nothing across a sample of standard library functions

### 4. Test vectors

- [ ] 4.1 Create `subset/metric-vectors.toml` keyed by metric identifier, with a header comment stating that vectors are the normative counting rule
- [ ] 4.2 Write vectors for `SM01` and `SM02` covering every enumerated disagreement construct: `and`/`or` sequences, `elif` chains, `else`, `except` handlers, conditional expressions, comprehension `if` clauses, `match` cases, and nested definitions
- [ ] 4.3 Write vectors for `SM03`, `SM04`, and `SM05`, including a single statement spread over many lines and a reformatted call that changes line span without changing statement count
- [ ] 4.4 Implement vector validation that fails naming the metric, the vector, the expected value, and the computed value
- [ ] 4.5 Implement coverage validation over vectors: fail when a metric lacks a vector for one of the enumerated disagreement constructs
- [ ] 4.6 Add the discriminating tests from the specs: a twelve-case flat `match` scoring below a four-level nest, and a guard-clause rewrite falling below the nesting threshold

### 5. Calibration

- [ ] 5.1 Add a calibration script that walks the pinned interpreter's standard library, excluding test packages, and reports per-metric distributions with percentiles
- [ ] 5.2 Run the calibration and record the distributions, including how much of the corpus each candidate threshold would flag
- [ ] 5.3 Choose a percentile per metric — not one percentile globally — and record the reasoning, rejecting any threshold that would flag nothing in the corpus as decoration
- [ ] 5.4 Compare each chosen threshold against the corresponding existing default recorded in the Prior Art section above (ruff `C901`/`PLR09xx`/`PLR1702`, flake8-cognitive-complexity, flake8-functions, NIST 500-235's risk bands) and record, per metric, whether the calibrated threshold lands near, above, or below the external default and why
- [ ] 5.5 Set the five thresholds and write each `calibration` record with corpus, percentile, and measurement date
- [ ] 5.6 Implement calibration validation: every threshold has a provenance record, and validation fails without one
- [ ] 5.7 Add a test that re-runs the calibration on the pinned interpreter and reproduces the recorded distribution without network access
- [ ] 5.8 Sanity-check the thresholds by hand against a handful of standard library functions a reviewer would agree are too complex, and record any threshold the numbers fail to justify

### 6. Reference integration

- [ ] 6.1 Extend `src/simplified_python/reference.py` with a metrics section rendering identifier, slug, region, threshold, counting rule, calibration provenance, and a worked example with its computed value
- [ ] 6.2 Derive metric anchors from the metric identifier alone, and add metrics to the document index alongside construct rules
- [ ] 6.3 Add the statement that the metric set is curated and carries no completeness guarantee, contrasted with provable construct coverage
- [ ] 6.4 Add the statement that cognitive complexity is defined locally and is not comparable with third-party tools
- [ ] 6.5 Confirm generation stays deterministic with metrics present: two runs byte-identical, input file order irrelevant
- [ ] 6.6 Regenerate and commit `docs/subset.md`, confirming the existing staleness check now covers the metrics section

### 7. Closeout

- [ ] 7.1 Confirm CI runs metric validation, vector validation, and the calibration reproduction test on the pinned interpreter
- [ ] 7.2 Append every `SM` identifier to `subset/published-ids.toml` and raise the rule-set version
- [ ] 7.3 Record in `AGENTS.md` how to add a metric: catalogue record, reference implementation, vectors, calibration, regenerate
- [ ] 7.4 Traceability pass: confirm every scenario in the Requirements section maps to a test, and list any that does not
