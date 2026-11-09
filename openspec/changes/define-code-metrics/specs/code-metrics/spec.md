## ADDED Requirements

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
