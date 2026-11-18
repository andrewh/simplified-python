# Agent skill and checker design

Design record for the agent skill in `skills/simplified-python/` and the checker in `src/simplified_python/check.py`. For how the checker works today, see [How the checker works](../checker.md).

## Why

The subset exists so that AI-written Python is cheap to review, but nothing yet tells an agent to write it. The [subset design](subset.md) explicitly deferred "agent-facing prompt guidance" and "the checker or CLI". Without them, an agent in another repository has no way to learn the dialect, and no way to confirm its output conforms.

Loading `docs/subset.md` (about 36 KB) into every session is too expensive, and a hand-written summary would drift from the registry. The skill must therefore be small, generated from the registry, and paired with a mechanical check, so the agent does not have to police itself by reading alone.

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
- `--restricted` is noisy by nature: assignments (SP203), comparisons (SP110) and comprehensions (SP117) are restricted, so nearly every line is listed. That is why it is opt-in, and why the skill calls it a checklist rather than a gate. Checking conditions in code later removed most of this noise; see [Checking restricted conditions in code](#checking-restricted-conditions-in-code).
- The pre-release notice said no checker existed. It then said the checker enforces only the banned rules, and now says it also enforces some restricted conditions, in `reference.py`, the README and (through the generator) the skill; a test keeps the copies identical.

## Checking restricted conditions in code

### Why

The first version of the checker enforced only banned rules and listed restricted constructs, with `--restricted`, as a manual-review checklist. That checklist is noisy: assignments, comparisons, comprehensions, and `except` clauses are all restricted, so nearly every line of real code appears on it. Several restricted conditions are structural facts about a single AST node, such as the number of comparison operators or assignment targets. Leaving them to a reviewer spends attention on exactly what a machine verifies reliably.

### Decisions

- **Condition checks for twelve restricted rules.** The checker verifies the conditions of SP110 `single-comparison`, SP114 `flat-conditional-expression`, SP115 `starred-unpacking`, SP116 `lambda-as-argument`, SP117 `simple-comprehensions`, SP203 `single-target-assignment`, SP406 `forwarding-varargs`, SP407 `forwarding-kwargs`, SP408 `nested-functions-without-closures`, SP503 `single-base-class`, SP603 `shallow-relative-imports`, and SP702 `typed-except-handlers`. An occurrence that breaks the condition is an error, reported with the condition, and fails the run like a banned construct. An occurrence that meets it is verified and is not listed for review. Each check sees the matched node, its parent, and its nearest enclosing function. SP116 needs the parent to see the enclosing call, SP406 and SP407 need it to see the function body, and SP408 needs the enclosing function to know which names a nested function may not use.
- **One error per nested conditional chain.** SP114 reports the outermost conditional expression of a chain such as `a if b else c if d else e`. A conditional nested directly in another is judged as part of the outer one.
- **Forwarding means exactly one use.** For SP406 and SP407, the parameter name must appear exactly once in the body, as `*args` or `**kwargs` in a call. A function that never uses the parameter breaks the condition, as does one that rebinds it. Uses are tracked by Python's scoping rules, so a nested function, class, or comprehension that binds the same name is a different variable.
- **Unchecked restricted rules stay review items.** The other restricted rules keep their current behaviour: listed only with `--restricted`, never failing the run.
- **Documentation marks checked conditions.** The reference states for each restricted rule whether the checker verifies its condition. The README summary and the skill digest label checked conditions *Condition (checked)*. The pre-release notice and the skill workflow describe the new scope.
- **flake8 plugin.** The prototype plugin shares the checker's logic, so it reports broken conditions by default too.
- **SP408 allows nested helpers.** A nested function may use a name its enclosing function binds exactly once, by `def`. Nested helpers may call each other and recurse; capturing any other parameter or local variable is still an error, and so is using a helper name that is also rebound, or defined inside a loop, where each pass rebinds it. A class body between the two functions does not hide an outer name, because methods cannot see class-level names, and a nested function's own type parameters do hide outer names.

Explicitly **not** included: the decorator allowlist checks (SP405, SP504), registry schema changes, and autofix.

### Impact

- **Behaviour:** code that passed the checker before can now fail it. `examples/rewrite/before.py` now also fails SP110, SP114, SP115, SP116, and SP702, which its comments already cited. Every conforming example still passes.
- **Code:** `CONDITIONS` in `src/simplified_python/check.py` maps rule identifiers to predicates. `check.py` stays standard-library only.
- **Generated files:** `docs/subset.md`, the README summary, and `skills/simplified-python/` are regenerated.
- **Ruleset version:** raised to 2. No rule is added or removed and no status changes, but the SP408 condition is loosened so that nested helpers defined once by `def` may call each other and themselves. That changes what conforms, so it is recorded as a rule-set change.
