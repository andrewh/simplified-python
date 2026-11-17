# Check Restricted Conditions in Code

## Why

`add-agent-skill` shipped a checker that enforces only banned rules and lists restricted constructs, with `--restricted`, as a manual-review checklist. That checklist is noisy: assignments, comparisons, comprehensions, and `except` clauses are all restricted, so nearly every line of real code appears on it. Several restricted conditions are structural facts about a single AST node, such as the number of comparison operators or assignment targets. Leaving them to a reviewer spends attention on exactly what a machine verifies reliably.

## What Changes

- **Condition checks for seven restricted rules.** The checker verifies the conditions of SP110 `single-comparison`, SP114 `flat-conditional-expression`, SP117 `simple-comprehensions`, SP203 `single-target-assignment`, SP503 `single-base-class`, SP603 `shallow-relative-imports`, and SP702 `typed-except-handlers`. An occurrence that breaks the condition is an error, reported with the condition, and fails the run like a banned construct. An occurrence that meets it is verified and is not listed for review.
- **Unchecked restricted rules stay review items.** The other restricted rules keep their current behaviour: listed only with `--restricted`, never failing the run.
- **Documentation marks checked conditions.** The reference states for each restricted rule whether the checker verifies its condition. The README summary and the skill digest label checked conditions *Condition (checked)*. The pre-release notice and the skill workflow describe the new scope.
- **flake8 plugin.** The prototype plugin shares the checker's logic, so it reports broken conditions by default too.

Explicitly **not** in this change: conditions that need scope or data-flow analysis (SP115, SP116, SP405 to SP408, SP504), registry schema changes, and autofix.

## Capabilities

### Modified Capabilities

- `subset-checker`: fails on broken checked conditions; restricted review items are limited to unchecked rules.
- `subset-skill`: the digest marks checked conditions and the workflow describes what a clean run proves.

## Impact

- **Behaviour:** code that passed the checker before can now fail it. `examples/rewrite/before.py` now also fails SP110, SP114, and SP702, which its comments already cited. Every conforming example still passes.
- **Code:** `CONDITIONS` in `src/simplified_python/check.py` maps rule identifiers to predicates. `check.py` stays standard-library only.
- **Generated files:** `docs/subset.md`, the README summary, and `skills/simplified-python/` are regenerated.
- **Ruleset version:** unchanged. No rule is added or removed, and no status changes.
