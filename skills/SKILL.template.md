---
name: simplified-python
description: Write, rewrite, or review Python in the "simplified Python" subset, a Python {{PYTHON_VERSION}} subset that bans or restricts constructs that are costly to review (star imports, chained comparisons, nested closures, and more) and is checked by rule IDs like SP601. Use when the user asks for simplified Python, cites an SP rule, or the project adopts the subset.
---

# Simplified Python

A conforming file is ordinary Python {{PYTHON_VERSION}} with unchanged behaviour. The subset only removes or narrows constructs, so that a human can review AI-written code quickly. Rule-set version {{RULESET_VERSION}}.

{{PRERELEASE}}

## When to apply

Apply the subset when the user or the project asks for it, or when you are editing a file that already follows it. Do not apply it to ordinary Python work otherwise.

## Workflow

1. Write the code using only allowed constructs, and restricted ones only when their condition holds. Prefer the replacement the rule names.
2. Run the checker on everything you wrote or changed, from this skill's directory:

   ```sh
   uv run --python {{PYTHON_VERSION}} <skill-dir>/check.py PATH...
   ```

   It prints `file:line:col: error SPxxx slug: ...` with the replacement for each banned construct and exits 1. Fix every one and run it again until it exits 0. Exit 2 means a file did not parse or the wrong Python ran; nothing was checked.
3. Review restricted constructs by hand. The checker does not verify their conditions. `--restricted` lists every occurrence as a checklist. It is noisy, because common constructs such as assignments and comprehensions are restricted.
4. A clean checker run only proves that no banned construct is present. Do not say the code "conforms" until step 3 is done.
5. When you rewrite existing code, cite the rule identifiers you removed, in your summary or in a comment, for example `# was SP118`.
6. If a task seems to need a banned construct, stop and ask. Do not use it silently, and do not work around the rule with a construct that has the same effect.

## Principles

Every restricted or banned rule serves at least one of these:

{{PRINCIPLES}}

## Banned

These must not appear.

{{BANNED}}

## Restricted

These may appear only when the condition holds.

{{RESTRICTED}}

## Allowed

No conditions: {{ALLOWED}}.

Anything not named above is classified by the same registry; look it up in [reference.md](reference.md) rather than guessing.

## Reference and examples

- [reference.md](reference.md): every rule with rationale and compliant and violating examples. Rules link to anchors such as `reference.md#sp601`.
- [examples/before.py](examples/before.py) and [examples/after.py](examples/after.py): the same program in full Python (breaking SP118, SP208, SP304 and SP601 on purpose) and rewritten in the subset. They print the same output.
