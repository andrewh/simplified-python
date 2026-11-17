## ADDED Requirements

### Requirement: Skill marks checked conditions
The skill digest SHALL label each restricted rule whose condition the checker verifies, and the workflow SHALL state that a clean run proves no banned construct is present and every checked condition holds, and that the other conditions still need manual review.

#### Scenario: Checked rule in the digest
- **WHEN** the skill is generated
- **THEN** the entry for single-target-assignment is labelled *Condition (checked)*
- **AND** the entry for function-decorator-allowlist is labelled *Condition*
