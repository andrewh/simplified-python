## ADDED Requirements

### Requirement: Reference is generated from the registry
`docs/subset.md` SHALL be produced from the rule registry by a generator command, and SHALL NOT be hand-edited. The document SHALL begin with a banner stating that it is generated, naming the command that regenerates it, and naming the registry as the place to make changes.

#### Scenario: Reader opens the reference
- **WHEN** a reader opens `docs/subset.md`
- **THEN** the first lines state that the file is generated, how to regenerate it, and where the rules live

#### Scenario: Generator is run
- **WHEN** the generator command runs against the registry
- **THEN** `docs/subset.md` is written with an entry for every rule in the registry

#### Scenario: Registry fails validation
- **WHEN** the generator runs against a registry that does not pass validation
- **THEN** generation fails and no partial document is written

### Requirement: Reference output is deterministic
Generation SHALL be deterministic: the same registry SHALL produce a byte-identical document on every run, on any machine, independent of file iteration order. Rules SHALL be ordered by identifier within each category, and categories SHALL appear in a fixed declared order.

#### Scenario: Generator runs twice
- **WHEN** the generator runs twice against an unchanged registry
- **THEN** both runs produce byte-identical output

#### Scenario: Registry files are read in a different order
- **WHEN** the underlying filesystem returns registry files in a different order
- **THEN** the generated document is unchanged

### Requirement: Rule entry content
Each rule entry in the reference SHALL show the rule identifier, the slug, the status, the construct in plain language, the rationale, the cited principles as links to their statements, and the rule's examples. A `restricted` entry SHALL show its condition. A `banned` entry SHALL show its replacement guidance next to the violating example, so a reader sees the rejected form and the sanctioned form together.

#### Scenario: Reader inspects a banned rule
- **WHEN** a reader opens the entry for a `banned` rule
- **THEN** the entry shows the violating example and the sanctioned alternative together with the rationale

#### Scenario: Reader inspects a restricted rule
- **WHEN** a reader opens the entry for a `restricted` rule
- **THEN** the entry states the condition under which the construct is permitted, with a compliant and a violating example

#### Scenario: Reader follows a principle citation
- **WHEN** a reader selects a principle citation in a rule entry
- **THEN** the reader is taken to that principle's statement in the same document

#### Scenario: Examples are rendered as code
- **WHEN** an entry shows an example
- **THEN** the snippet is rendered as a fenced Python code block, unmodified from the registry

### Requirement: Principles are stated in full
The reference SHALL include a section stating every review principle in the registry, each with its identifier and the review cost it addresses, placed before the rule entries so a reader meets the reasoning before the rules.

#### Scenario: Reader reads the principles
- **WHEN** a reader opens the reference
- **THEN** the principles section appears before the rule entries and states every principle the registry defines

#### Scenario: Principle is added to the registry
- **WHEN** a new principle is added and the generator runs
- **THEN** the principles section includes it without further edits

### Requirement: Rule index for scanning
The reference SHALL include an index listing every rule as a row with its identifier, slug, and status, linking to the rule's entry, so a reviewer can scan the whole subset without reading each entry.

#### Scenario: Reviewer scans the subset
- **WHEN** a reviewer opens the reference and reads the index
- **THEN** every rule appears once with its identifier, slug, and status, linked to its entry

#### Scenario: Reviewer filters by status
- **WHEN** a reviewer looks for banned constructs
- **THEN** the status column allows the banned rules to be identified from the index alone

### Requirement: Rules are citable by stable link
Every rule entry SHALL have a stable in-document anchor derived from its identifier, so a review comment can link directly to a rule. The anchor SHALL not change when the rule's rationale, examples, or position in the document change.

#### Scenario: Reviewer cites a rule
- **WHEN** a reviewer links to a rule's anchor in a review comment
- **THEN** the link resolves to that rule's entry in the reference

#### Scenario: Rule text is revised
- **WHEN** a rule's rationale or examples change and the document is regenerated
- **THEN** the rule's anchor is unchanged and existing links still resolve

### Requirement: README carries a generated summary
`README.md` SHALL contain a summary of the subset generated from the registry by the same generator command, placed between fixed begin and end markers. The summary SHALL list every `banned` rule with its replacement and every `restricted` rule with its condition, and each listed rule SHALL link to its entry in `docs/subset.md`. Text outside the markers SHALL NOT be changed by the generator, and text between the markers SHALL NOT be hand-edited.

#### Scenario: Reader opens the README
- **WHEN** a reader opens `README.md`
- **THEN** it lists every banned and restricted rule, each linked to its full entry in the reference

#### Scenario: README markers are missing
- **WHEN** the generator runs and `README.md` lacks the summary markers
- **THEN** generation fails with an error naming the missing markers and nothing is written

#### Scenario: README summary is stale or hand-edited
- **WHEN** the text between the markers differs from freshly generated output
- **THEN** validation fails with a message instructing the author to run the generator

### Requirement: Reference cannot go stale
Validation SHALL regenerate the reference and compare it against the committed file, and SHALL fail when the two differ, reporting that the document must be regenerated. This check SHALL run in continuous integration.

#### Scenario: Registry changes without regeneration
- **WHEN** a rule is edited and the reference is not regenerated
- **THEN** validation fails with a message instructing the author to run the generator

#### Scenario: Reference is edited by hand
- **WHEN** the committed reference is edited directly
- **THEN** validation fails, because the file no longer matches the registry

#### Scenario: Registry and reference agree
- **WHEN** the committed reference matches freshly generated output
- **THEN** validation passes
