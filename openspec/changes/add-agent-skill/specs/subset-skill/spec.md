## ADDED Requirements

### Requirement: Skill is generated from the registry
`skills/simplified-python/` SHALL be produced by a generator command from the registry plus one hand-written template, and its generated files SHALL NOT be edited by hand. The generator SHALL write nothing when the registry is invalid.

#### Scenario: Generator is run
- **WHEN** the generator runs against a valid registry
- **THEN** `SKILL.md`, `reference.md`, `rules.json`, `check.py`, and the example files are written

#### Scenario: Registry is invalid
- **WHEN** the generator runs against a registry that fails validation
- **THEN** it reports the errors and writes nothing

### Requirement: Skill is a loadable skill
`SKILL.md` SHALL begin with frontmatter giving `name` and a `description` that says what the skill does and when to use it, so an agent can decide to load it.

#### Scenario: Agent lists skills
- **WHEN** an agent reads the frontmatter
- **THEN** it can tell the skill applies to writing or reviewing Python in the simplified subset

### Requirement: Digest covers every restriction
The `SKILL.md` digest SHALL list the principles, every banned rule with its replacement, and every restricted rule with its condition, each with identifier and slug. It SHALL name every allowed rule by slug only, and SHALL link to the full reference for rationale and examples.

#### Scenario: Rule is banned in the registry
- **WHEN** a rule is banned in the registry
- **THEN** the digest lists it with its replacement

#### Scenario: Allowed rule
- **WHEN** a rule is allowed
- **THEN** it appears only as a slug, without prose

### Requirement: Skill states its limits and workflow
The hand-written text SHALL tell the agent: when to apply the subset, to run the checker before finishing, to verify restricted conditions by hand, to cite rule identifiers when rewriting, to ask rather than violate a rule when a task seems to need a banned construct, and that a clean checker run does not prove restricted conditions hold. It SHALL carry the pre-release notice.

#### Scenario: Agent finishes writing code
- **WHEN** an agent follows the skill
- **THEN** it runs the checker, fixes violations, and reviews restricted constructs by hand before reporting done

### Requirement: Skill is self-contained and versioned
The skill directory SHALL contain everything it references, so that copying it to another location leaves every link and command working. It SHALL state the rule-set version and Python version it was generated from.

#### Scenario: Skill is copied elsewhere
- **WHEN** the directory is copied to another agent's skills directory
- **THEN** the checker command and every relative link in `SKILL.md` still resolve

### Requirement: Skill is kept up to date
The generator SHALL offer a `--check` mode that fails when any generated file differs from what the registry would produce, and CI SHALL run it.

#### Scenario: Registry changes without regeneration
- **WHEN** a rule changes and the skill is not regenerated
- **THEN** `--check` fails and names the stale files

#### Scenario: Output is deterministic
- **WHEN** the generator runs twice on an unchanged registry
- **THEN** both outputs are byte-identical
