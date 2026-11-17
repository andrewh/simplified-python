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

#### Scenario: Nested conditional chain
- **WHEN** the checker runs on `v = a if b else c if d else e if f else g`
- **THEN** it reports one error for the flat-conditional-expression rule, at the outermost conditional expression

#### Scenario: Forwarded variadic arguments
- **WHEN** a function declares `*args` or `**kwargs` and its body uses the name exactly once, as `*args` or `**kwargs` in a call
- **THEN** the checker reports nothing for the forwarding rule
- **AND** any other use, a second use, or no use is reported as an error

#### Scenario: Nested function uses an enclosing name
- **WHEN** a function defined inside another function uses a parameter or local variable of the enclosing function, including another nested function or itself
- **THEN** the checker reports an error for the nested-functions-without-closures rule at the nested function
- **AND** a nested function that uses only its own names, globals, and builtins is not reported

#### Scenario: Violating examples of checked rules are flagged
- **WHEN** the checker runs on each violating example of a restricted rule whose condition it checks
- **THEN** it reports that rule as an error

## MODIFIED Requirements

### Requirement: Restricted constructs are review items
The checker SHALL NOT fail on restricted constructs whose condition it does not check. With `--restricted` it SHALL list each occurrence of such a construct with the rule's condition, as an item for manual review. Output SHALL state how many restricted conditions are not checked.

#### Scenario: Restricted listing is requested
- **WHEN** the checker runs with `--restricted` on a file using a decorated function
- **THEN** the decorator is listed with its rule's condition and labelled as needing manual review
- **AND** the exit status is unaffected by it

#### Scenario: Restricted listing is not requested
- **WHEN** the checker runs without `--restricted`
- **THEN** no unchecked restricted construct is listed
