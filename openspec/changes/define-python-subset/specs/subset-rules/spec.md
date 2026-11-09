## ADDED Requirements

### Requirement: Registry is the single source of truth
The subset SHALL be defined exclusively by rule records stored as TOML under `subset/rules/`. No other artifact — prose document, code comment, checker implementation, or README — SHALL define, add to, or override a subset rule. The registry MUST be readable using only the Python standard library.

#### Scenario: Rule exists only in the registry
- **WHEN** a consumer needs to know whether a construct is permitted
- **THEN** the answer is derived from the rule records under `subset/rules/` and from no other source

#### Scenario: Prose claim contradicts the registry
- **WHEN** a document or comment describes a restriction that has no corresponding rule record
- **THEN** that restriction is not part of the subset and carries no normative weight

#### Scenario: Registry is loaded without third-party packages
- **WHEN** the registry is loaded in an environment with no installed dependencies
- **THEN** loading succeeds using standard library TOML parsing only

### Requirement: Rule record schema
Every rule record SHALL declare the fields `id`, `slug`, `category`, `construct` (the construct in plain language), `anchor`, `status`, and `rationale`, plus `principles`, `condition`, and `replacement` where the status requires them, and at least one example, given as lists of snippets in `compliant` and `violating`. The loader SHALL reject any record that omits a required field, declares an unknown field, or supplies a field of the wrong type, and the error MUST name the offending file and rule `id`.

#### Scenario: Required field is missing
- **WHEN** a rule record omits `rationale`
- **THEN** loading fails with an error naming the source file and the rule `id`

#### Scenario: Unrecognised field is present
- **WHEN** a rule record declares a field that is not part of the schema
- **THEN** loading fails rather than ignoring the field silently

#### Scenario: Field has the wrong type
- **WHEN** a rule record supplies `principles` as a string instead of a list of strings
- **THEN** loading fails with an error naming the field, the source file, and the rule `id`

### Requirement: Construct anchors resolve to real grammar nodes
Every rule SHALL anchor to one or more concrete CPython AST node types that exist in the target grammar version, identified by their `ast` class names, so that closely related constructs can be governed by a single reviewable rule. A rule MAY narrow its anchor to an attribute of the anchored nodes (for example the `names` attribute of `ImportFrom`, or the `comparators` attribute of `Compare`); a narrowed anchor SHALL apply to that attribute on every node type it lists. A narrowed anchor MAY also declare a `value`; the anchored construct is then present only where the attribute equals that value (for example `alias` narrowed by `name` with value `"*"` for a star import), and otherwise it is present wherever the attribute is non-empty. The loader SHALL reject an empty node list, node names that do not resolve against the `ast` module of the target version, attributes that any listed node type does not define, and a `value` declared without an attribute.

#### Scenario: Anchor names a node that does not exist
- **WHEN** a rule anchors to an AST class name absent from the target version
- **THEN** loading fails with an error naming the unresolved node

#### Scenario: Anchor groups related node types
- **WHEN** a rule anchors to the arithmetic operator nodes `Add`, `Sub`, `Mult`, `Div`, `FloorDiv`, `Mod`, and `Pow`
- **THEN** the anchor is accepted and the rule classifies every node type it lists

#### Scenario: Anchor is narrowed to an attribute
- **WHEN** a rule anchors to `ImportFrom` narrowed by the attribute `names`
- **THEN** the anchor is accepted and the rule applies only to that attribute of that node type

#### Scenario: Narrowed anchor matches an attribute value
- **WHEN** a rule anchors to `alias` narrowed by the attribute `name` with value `"*"`
- **THEN** the anchored construct is present in `from os import *` and absent from `from os import path`

#### Scenario: Attribute does not exist on a listed node
- **WHEN** a rule narrows an anchor by an attribute that one of its listed node types does not define
- **THEN** loading fails with an error naming the node type and the invalid attribute

#### Scenario: Anchor lists no nodes
- **WHEN** a rule declares an empty node list
- **THEN** loading fails with an error naming the rule `id`

### Requirement: Three rule statuses with fixed meanings
Every rule SHALL carry exactly one status from `allowed`, `restricted`, or `banned`, where `allowed` means the construct may be used without further conditions, `restricted` means the construct is permitted only when a stated condition holds, and `banned` means the construct must not appear. A `restricted` rule MUST state its condition in a `condition` field, expressed so that a reader can evaluate it from the source text alone. A `banned` rule MUST state the sanctioned alternative in a `replacement` field. An `allowed` rule MUST NOT declare `condition` or `replacement`. The status field SHALL reject any other value.

#### Scenario: Restricted rule omits its condition
- **WHEN** a rule has status `restricted` and no `condition` field
- **THEN** loading fails with an error naming the rule `id`

#### Scenario: Banned rule omits its replacement
- **WHEN** a rule has status `banned` and no `replacement` field
- **THEN** loading fails with an error naming the rule `id`

#### Scenario: Allowed rule carries a condition
- **WHEN** a rule has status `allowed` and declares a `condition` field
- **THEN** loading fails, because a conditional permission must be recorded as `restricted`

#### Scenario: Status value is outside the fixed set
- **WHEN** a rule declares a status such as `discouraged` or `warning`
- **THEN** loading fails with an error listing the three permitted statuses

### Requirement: Rules cite review principles
The registry SHALL enumerate the review principles that justify narrowing Python, each with a stable identifier and a statement of the review cost it addresses. Every rule with status `restricted` or `banned` SHALL cite at least one principle identifier. The loader SHALL reject a citation of an unknown principle identifier, and SHALL reject a `restricted` or `banned` rule that cites none.

#### Scenario: Banned rule cites no principle
- **WHEN** a rule has status `banned` and an empty `principles` list
- **THEN** loading fails with an error naming the rule `id`

#### Scenario: Rule cites an unknown principle
- **WHEN** a rule cites a principle identifier that the registry does not define
- **THEN** loading fails with an error naming the unknown identifier

#### Scenario: Principle is retrieved for a rule
- **WHEN** a consumer reads a banned rule
- **THEN** the cited principle identifiers resolve to principle statements held in the registry

### Requirement: Stable unique rule identifiers
Every rule SHALL have an identifier of the form `SP` followed by three digits, allocated from a numeric block reserved for the rule's category, and a lowercase hyphenated `slug` that reads as the rule's name. Identifiers and slugs SHALL be unique across all registry files. An identifier that has been retired SHALL be recorded as retired and SHALL NOT be reassigned to a different rule.

#### Scenario: Identifier is duplicated across files
- **WHEN** two rule records in different registry files share the identifier `SP204`
- **THEN** loading fails with an error naming the identifier and both files

#### Scenario: Identifier falls outside its category block
- **WHEN** a rule in the `imports` category takes an identifier from the block reserved for `expressions`
- **THEN** loading fails with an error naming the rule and the expected block

#### Scenario: Retired identifier is reused
- **WHEN** a new rule claims an identifier listed as retired
- **THEN** loading fails with an error stating that retired identifiers are never reassigned

#### Scenario: Slug is duplicated
- **WHEN** two rule records share the same `slug`
- **THEN** loading fails with an error naming the slug and both rule identifiers

### Requirement: Exhaustive coverage of the target grammar
Every concrete AST node type that can appear in a tree produced by `ast.parse` in `exec` mode on the target version SHALL be classified by exactly one rule that anchors it without narrowing to an attribute. Validation SHALL enumerate those node types from the live `ast` module rather than from a hand-maintained list, and SHALL fail when any node type is unclassified or is classified by more than one unnarrowed rule. The failure message MUST list every offending node type by name.

#### Scenario: Grammar node has no rule
- **WHEN** validation runs and a reachable node type such as `TemplateStr` has no rule
- **THEN** validation fails and the message lists that node type

#### Scenario: Grammar node has two base rules
- **WHEN** two rules anchor to the same node type without narrowing to an attribute
- **THEN** validation fails, because the status of that construct would be ambiguous

#### Scenario: Narrowed rules coexist with a base rule
- **WHEN** a node type has one unnarrowed rule and one or more rules narrowed to an attribute
- **THEN** validation succeeds, because the unnarrowed rule establishes the construct's status

#### Scenario: New grammar node appears after an upgrade
- **WHEN** the target version is raised and the new version introduces a node type
- **THEN** validation fails until that node type is classified

### Requirement: Justified exclusions from coverage
Node types that cannot appear in a tree produced by `ast.parse` in `exec` mode — deprecated placeholders, alternate parse roots, and nodes produced only under opt-in parse flags — SHALL be listed in `subset/exclusions.toml`, each with a reason and an exclusion category. Validation SHALL reject an exclusion that lacks a reason, and SHALL reject any node type that is both excluded and classified by a rule.

#### Scenario: Exclusion lacks a reason
- **WHEN** a node type is listed in the exclusions file with no reason
- **THEN** validation fails with an error naming that node type

#### Scenario: Node is both excluded and ruled on
- **WHEN** a node type appears in the exclusions file and also carries a rule
- **THEN** validation fails, because the node's treatment is contradictory

#### Scenario: Excluded node keeps coverage satisfied
- **WHEN** a justified exclusion covers a deprecated placeholder node such as `AugLoad`
- **THEN** coverage validation passes without a rule for that node

### Requirement: Target grammar version is declared and enforced
The registry SHALL declare the Python version whose grammar it defines. Validation that depends on the live `ast` module SHALL run only on an interpreter matching the declared version, and SHALL fail with a message naming the required version when the running interpreter does not match. Validation SHALL NOT be skipped silently on a mismatched interpreter.

#### Scenario: Validation runs on the declared version
- **WHEN** validation runs on an interpreter matching the declared version
- **THEN** grammar coverage is computed from that interpreter's `ast` module

#### Scenario: Validation runs on a different version
- **WHEN** validation runs on an interpreter whose version differs from the declared version
- **THEN** validation fails with a message naming the declared version and the running version

### Requirement: Examples are valid and discriminating
Every rule SHALL carry at least one compliant example, and every `restricted` or `banned` rule SHALL also carry at least one violating example. Every example SHALL parse under the target version. Each violating example SHALL contain the rule's anchored construct, and a compliant example for a `banned` rule SHALL NOT contain it. Validation SHALL fail on any example that does not meet these conditions, naming the rule and the example.

#### Scenario: Example does not parse
- **WHEN** an example snippet is not valid Python under the target version
- **THEN** validation fails with the syntax error, the rule `id`, and which example failed

#### Scenario: Violating example lacks the construct
- **WHEN** a violating example does not contain the rule's anchored construct
- **THEN** validation fails, because the example does not demonstrate the rule

#### Scenario: Compliant example contains a banned construct
- **WHEN** the compliant example of a `banned` rule contains that rule's anchored construct
- **THEN** validation fails, because the example contradicts the rule

#### Scenario: Banned rule has no violating example
- **WHEN** a rule has status `banned` and no violating example
- **THEN** validation fails with an error naming the rule `id`

### Requirement: Subset never extends Python
The registry SHALL only remove or narrow constructs available in the target Python version. No rule SHALL describe syntax that stock Python does not accept, and no rule SHALL assign a construct a meaning that differs from its meaning in Python. Consequently every compliant example SHALL be accepted by stock `ast.parse` at the target version with no preprocessing.

#### Scenario: Compliant example requires non-Python syntax
- **WHEN** a compliant example only parses after preprocessing or with a non-standard parser
- **THEN** validation fails, because the subset adds no syntax

#### Scenario: Conforming program runs on stock Python
- **WHEN** a program conforms to every rule in the registry
- **THEN** it is a valid Python program at the target version with unchanged runtime semantics

### Requirement: Versioned rule set with recorded changes
The registry SHALL declare a rule-set version. Adding a rule, changing a rule's status, or removing a rule SHALL require raising that version and recording the change, and removal SHALL require recording the identifier as retired. Validation SHALL fail when a previously published identifier is absent from both the rule records and the retired list.

#### Scenario: Rule status changes
- **WHEN** a rule moves from `restricted` to `banned`
- **THEN** the rule-set version is raised and the change is recorded with the rule `id`

#### Scenario: Rule disappears without being retired
- **WHEN** a previously published identifier is absent from the rule records and is not listed as retired
- **THEN** validation fails with an error naming the missing identifier

#### Scenario: Consumer reads the rule-set version
- **WHEN** a downstream tool loads the registry
- **THEN** the rule-set version and target grammar version are available from the loaded data
