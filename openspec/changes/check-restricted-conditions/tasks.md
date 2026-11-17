# Tasks: Check Restricted Conditions in Code

## 1. Checker

- [x] 1.1 Add `CONDITIONS` to `check.py`: predicates for SP110, SP114, SP116, SP117, SP203, SP406, SP407, SP503, SP603, and SP702, each given the matched node and its parent
- [x] 1.1a Report one SP114 error per nested conditional chain
- [x] 1.2 Report a broken checked condition as an error with status `violated`, and exit 1 on it
- [x] 1.3 Stop listing restricted constructs whose condition is checked; keep `--restricted` for the rest
- [x] 1.4 Tests: each checked rule's violating examples fail and compliant ones pass, edge cases for each predicate, CLI exit status, `before.py` breaks exactly the checkable rules its comments cite, legacy-baseline parity for unchanged rules

## 2. Documentation

- [x] 2.1 Mark checked conditions in the reference, README summary, and skill digest
- [x] 2.2 Update the pre-release notice and the skill workflow text
- [x] 2.3 Regenerate `docs/subset.md`, the README summary, and `skills/simplified-python/`

## 3. Integration

- [x] 3.1 The flake8 plugin reports broken conditions by default
- [ ] 3.2 Run `openspec validate check-restricted-conditions --strict`
