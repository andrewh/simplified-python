## ADDED Requirements

### Requirement: Checker reports banned constructs
The checker SHALL parse each given Python file and report every occurrence of a construct matched by a `banned` rule. Each finding SHALL show the file, line, column, rule identifier, slug, and the rule's replacement guidance.

#### Scenario: File contains a banned construct
- **WHEN** the checker runs on a file containing `from os import *`
- **THEN** it reports that file, line, and column with the identifier and slug of the star-import rule and its replacement
- **AND** it exits with status 1

#### Scenario: File contains several violations
- **WHEN** a file breaks more than one banned rule, or one rule more than once
- **THEN** every occurrence is reported in a single run, ordered by file, line, and column

#### Scenario: File is conforming
- **WHEN** the checker runs on a file with no banned construct
- **THEN** it reports nothing as a violation and exits with status 0

### Requirement: Checker and registry agree on matching
The checker SHALL decide whether a construct matches a rule with the same predicate the registry uses to validate rule examples.

#### Scenario: Violating examples are flagged
- **WHEN** the checker runs on each violating example of a banned rule
- **THEN** it reports that rule

#### Scenario: Compliant examples are not flagged by their own rule
- **WHEN** the checker runs on each compliant example of a banned rule
- **THEN** it does not report that rule

### Requirement: Restricted constructs are review items
The checker SHALL NOT fail on restricted constructs. With `--restricted` it SHALL list each occurrence of a restricted construct with the rule's condition, as an item for manual review. Output SHALL state that restricted conditions are not checked.

#### Scenario: Restricted listing is requested
- **WHEN** the checker runs with `--restricted` on a file using a lambda
- **THEN** the lambda is listed with its rule's condition and labelled as needing manual review
- **AND** the exit status is unaffected by it

#### Scenario: Restricted listing is not requested
- **WHEN** the checker runs without `--restricted`
- **THEN** no restricted construct is listed

### Requirement: Files that cannot be checked are never clean
A file that does not parse, cannot be read, or cannot be checked on the running interpreter SHALL be reported as an error, and the checker SHALL exit with status 2.

#### Scenario: Syntax error
- **WHEN** the checker runs on a file with a syntax error
- **THEN** it reports the file and the syntax error and exits with status 2

#### Scenario: Wrong interpreter
- **WHEN** the running Python minor version differs from the rules' `python_version`
- **THEN** the checker reports both versions, checks nothing, and exits with status 2

### Requirement: Directories and multiple paths
The checker SHALL accept any number of files and directories. A directory SHALL be searched recursively for `*.py` files in sorted order.

#### Scenario: Directory is given
- **WHEN** the checker is given a directory
- **THEN** every `*.py` file beneath it is checked

### Requirement: Checker is self-contained
The checker SHALL depend only on the standard library and a rules snapshot, and SHALL NOT require the TOML registry or the repository.

#### Scenario: Run outside the repository
- **WHEN** `check.py` and `rules.json` are copied to an empty directory
- **THEN** the checker runs there and produces the same findings
