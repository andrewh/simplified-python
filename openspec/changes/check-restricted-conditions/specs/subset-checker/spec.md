## ADDED Requirements

### Requirement: Checker verifies checked restricted conditions
The checker SHALL verify the condition of each restricted rule it lists as checked. An occurrence that breaks the condition SHALL be reported as an error with the file, line, column, rule identifier, slug, and the rule's condition, and SHALL make the checker exit with status 1. An occurrence that meets the condition SHALL NOT be reported.

#### Scenario: Chained assignment
- **WHEN** the checker runs on a file containing `a = b = 0`
- **THEN** it reports an error for the single-target-assignment rule with its condition
- **AND** it exits with status 1

#### Scenario: Condition holds
- **WHEN** the checker runs on a file containing `x, y = point`
- **THEN** it reports nothing for the single-target-assignment rule, with or without `--restricted`

#### Scenario: Violating examples of checked rules are flagged
- **WHEN** the checker runs on each violating example of a restricted rule whose condition it checks
- **THEN** it reports that rule as an error

## MODIFIED Requirements

### Requirement: Restricted constructs are review items
The checker SHALL NOT fail on restricted constructs whose condition it does not check. With `--restricted` it SHALL list each occurrence of such a construct with the rule's condition, as an item for manual review. Output SHALL state how many restricted conditions are not checked.

#### Scenario: Restricted listing is requested
- **WHEN** the checker runs with `--restricted` on a file using a lambda
- **THEN** the lambda is listed with its rule's condition and labelled as needing manual review
- **AND** the exit status is unaffected by it

#### Scenario: Restricted listing is not requested
- **WHEN** the checker runs without `--restricted`
- **THEN** no unchecked restricted construct is listed
