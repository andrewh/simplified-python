# Design: Agent Skill and Banned-Construct Checker

## Context

Agents load a skill in layers: the frontmatter description is always visible, `SKILL.md` loads when the skill triggers, and linked files load only when read. The registry has 58 rules; the full reference is about 9k tokens, the banned and restricted rules alone about 1.5k.

## Decisions

**Generated digest, hand-written workflow.** `skills/SKILL.template.md` holds the prose (when to use, workflow, what to do when blocked) with placeholders. `skill.py` fills the digest from the registry. Hand-written text can then change without a registry change, and rules can change without anyone remembering to update the skill.

**Self-contained skill directory.** A skill installed into `~/.agents/skills/` has no repository next to it. So the directory carries everything it needs: `reference.md` (copy of `docs/subset.md`), `examples/` (copies of `rewrite/before.py` and `after.py`), `check.py`, and `rules.json`. Copies are generated and checked for staleness, never edited.

**One checker, data-driven, stdlib only.** `check.py` imports nothing from the package and reads `rules.json`. The same file is the module `simplified_python.check` in the repo and the script `check.py` in the skill (a byte-identical copy, verified). One code path means tests of the module cover the shipped script. Run it with `uv run --python 3.14 check.py FILE...`.

**Shared matcher.** The registry's `contains_construct` already decides whether an anchor matches. It is refactored over `find_constructs`, which yields matching nodes with positions. The checker uses the same function through `rules.json`, so "what the example tests prove a rule matches" and "what the checker flags" are the same predicate. Because `check.py` must stay import-free, the matcher lives in `check.py` and `registry.py` imports it.

**Positions.** Some anchored nodes carry no position (`Load`, operators). Matching walks the tree with the nearest enclosing position so every finding has a line and column.

**Banned fails, restricted informs.** Restricted conditions are prose. Failing on every restricted construct would flag nearly every file (every decorator, every comprehension), so the checker never fails on them. `--restricted` lists them as review items, which gives the agent a checklist of lines to verify by hand.

**Exit codes.** 0 clean, 1 banned construct found, 2 usage, syntax, or interpreter problem. A file that does not parse is reported and never counted as clean.

**Version honesty.** `rules.json` and `SKILL.md` carry `ruleset_version` and `python_version`. The checker refuses to run on a different Python minor version, since an older `ast` cannot parse or classify 3.14 syntax.

## Risks

- **False sense of conformance.** A clean checker run proves only that no banned construct is present. The skill and the checker output both say restricted conditions are unchecked.
- **Copy drift.** Mitigated by generation plus a test and a CI step.
- **No packaged install.** Distribution is copy or symlink for now; a published package is a separate change.

## Findings from implementation

- A finding points at the matched node, not the statement: the star-import ban reports the column of the `*` alias.
- `--restricted` is noisy by nature: assignments (SP203), comparisons (SP110) and comprehensions (SP117) are restricted, so nearly every line is listed. That is why it is opt-in, and why the skill calls it a checklist rather than a gate.
- The pre-release notice said no checker existed. It now says the checker enforces only the banned rules, in `reference.py`, the README and (through the generator) the skill; a test keeps the copies identical.
