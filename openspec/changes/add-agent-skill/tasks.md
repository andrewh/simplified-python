# Tasks: Add an Agent Skill and Banned-Construct Checker

## 1. Checker

- [x] 1.1 Add `src/simplified_python/check.py` (stdlib only): `find_constructs` yielding `(node, line, col)` with inherited positions, the rules snapshot loader, and `check_source`
- [x] 1.2 Refactor `registry.contains_construct` over `check.find_constructs`; the existing suite must stay green
- [x] 1.3 Add the CLI: files and directories, `--restricted`, `--rules`, exit codes 0/1/2, the interpreter-version gate, and findings sorted by file, line, column
- [x] 1.4 Tests: each banned rule's violating examples are flagged and compliant ones are not, restricted listing on and off, syntax error, wrong interpreter, directory recursion, every `examples/` file, and `before.py` flags exactly SP118, SP208, SP304, SP601

## 2. Skill generator

- [x] 2.1 Write `skills/SKILL.template.md` with the workflow guidance and placeholders for version and digest
- [x] 2.2 Add `src/simplified_python/skill.py`: render the digest, `rules.json` (banned and restricted rules only), and copies of `docs/subset.md`, `check.py`, and the rewrite examples into `skills/simplified-python/`
- [x] 2.3 Add `--check`, refuse to write on an invalid registry, and keep output deterministic
- [x] 2.4 Tests: frontmatter, digest completeness against the registry, allowed rules as slugs only, links resolve, determinism, stale detection, no write on invalid registry, and the skill copy of the checker works in an empty directory

## 3. Integration

- [x] 3.1 Generate `skills/simplified-python/` and commit it
- [x] 3.2 Add the `skill --check` step to CI
- [x] 3.3 Update `README.md` (install and use) and `AGENTS.md` (generated files, commands)
- [x] 3.4 Run `openspec validate add-agent-skill --strict`, the registry check, and the full suite
