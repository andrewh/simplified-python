---
name: simplified-python
description: Write, rewrite, or review Python in the "simplified Python" subset, a Python 3.14 subset that bans or restricts constructs that are costly to review (star imports, chained comparisons, nested closures, and more) and is checked by rule IDs like SP601. Use when the user asks for simplified Python, cites an SP rule, or the project adopts the subset.
---

# Simplified Python

A conforming file is ordinary Python 3.14 with unchanged behaviour. The subset only removes or narrows constructs, so that a human can review AI-written code quickly. Rule-set version 1.

> [!WARNING]
> **Experimental pre-release.** The subset is still being defined and is not ready for general use.
> Rule identifiers, statuses, and the registry format may change without notice between rule-set versions,
> and the checker enforces only the banned rules; restricted conditions still rely on human review.

## When to apply

Apply the subset when the user or the project asks for it, or when you are editing a file that already follows it. Do not apply it to ordinary Python work otherwise.

## Workflow

1. Write the code using only allowed constructs, and restricted ones only when their condition holds. Prefer the replacement the rule names.
2. Run the checker on everything you wrote or changed, from this skill's directory:

   ```sh
   uv run --python 3.14 <skill-dir>/check.py PATH...
   ```

   It prints `file:line:col: error SPxxx slug: ...` with the replacement for each banned construct and exits 1. Fix every one and run it again until it exits 0. Exit 2 means a file did not parse or the wrong Python ran; nothing was checked.
3. Review restricted constructs by hand. The checker does not verify their conditions. `--restricted` lists every occurrence as a checklist. It is noisy, because common constructs such as assignments and comprehensions are restricted.
4. A clean checker run only proves that no banned construct is present. Do not say the code "conforms" until step 3 is done.
5. When you rewrite existing code, cite the rule identifiers you removed, in your summary or in a comment, for example `# was SP118`.
6. If a task seems to need a banned construct, stop and ask. Do not use it silently, and do not work around the rule with a construct that has the same effect.

## Principles

Every restricted or banned rule serves at least one of these:

- **P1 local-reasoning**: The meaning of a piece of code can be worked out from the code on the screen.
- **P2 one-obvious-spelling**: Each behaviour has one usual way to write it.
- **P3 no-action-at-a-distance**: Code changes only the state and behaviour that it visibly names.
- **P4 bounded-reading-cost**: Each construct can be read once, from left to right and top to bottom, without unpacking it.

## Banned

These must not appear.

- [SP113](reference.md#sp113) `no-template-strings`: Template string literals (PEP 750): `t"Hello {name}"`. *Instead:* Use an f-string to build text. To escape or quote values, call the escaping function explicitly on each value.
- [SP118](reference.md#sp118) `no-walrus`: Assignment expressions (the walrus operator): `(match := pattern.search(line))`. *Instead:* Assign the value in its own statement on the line before, then use the name.
- [SP208](reference.md#sp208) `no-global-or-nonlocal`: The `global` and `nonlocal` declarations. *Instead:* Pass the value in as an argument and return the new value. To keep shared state, put it in an object that is passed explicitly.
- [SP304](reference.md#sp304) `no-loop-else`: An `else` clause on a `for` or `while` loop. *Instead:* Record the outcome in a variable inside the loop, then test that variable after the loop with an `if` statement.
- [SP502](reference.md#sp502) `no-class-keywords`: Keyword arguments in a class header: `class A(metaclass=Meta)`, `class B(Base, flag=True)`. *Instead:* Write the behaviour as explicit methods or as module-level functions. To check subclasses, call a check function explicitly after the class is defined.
- [SP601](reference.md#sp601) `no-star-import`: Importing every public name from a module with `from module import *`. *Instead:* Import the names you use explicitly, or import the module and qualify each name.
- [SP703](reference.md#sp703) `no-except-star`: The `try` statement with `except*` clauses for exception groups. *Instead:* Catch the `ExceptionGroup` with a normal `except` clause and inspect its `exceptions` attribute explicitly.
- [SP801](reference.md#sp801) `no-async`: Coroutines and asynchronous statements: `async def`, `await`, `async for`, `async with`. *Instead:* Write synchronous code. If concurrency is necessary, keep it outside code that must conform to the subset until async rules exist.
- [SP802](reference.md#sp802) `no-async-comprehension`: An `async for` clause in a comprehension: `[x async for x in stream]`. *Instead:* Write synchronous code; see SP801.

## Restricted

These may appear only when the condition holds.

- [SP110](reference.md#sp110) `single-comparison`: A comparison: `a < b`, `x == y`, `key in table`. *Condition:* A comparison uses exactly one comparison operator. Chained comparisons such as `a < b < c` are not permitted.
- [SP114](reference.md#sp114) `flat-conditional-expression`: A conditional expression: `a if condition else b`. *Condition:* The test and both branches of a conditional expression do not contain another conditional expression.
- [SP115](reference.md#sp115) `starred-unpacking`: Starred expressions: `f(*args)`, `[*head, *tail]`, `first, *rest = items`. *Condition:* A starred expression may unpack values into a call or a list, tuple, or set display. It must not be an assignment target or a `for` loop target.
- [SP116](reference.md#sp116) `lambda-as-argument`: Anonymous functions: `lambda item: item.size`. *Condition:* A lambda is permitted only as a direct argument of a call, such as `sorted(items, key=lambda item: item.size)`.
- [SP117](reference.md#sp117) `simple-comprehensions`: List, set, and dict comprehensions, generator expressions, and their `for` / `if` clauses. *Condition:* A comprehension has exactly one `for` clause and at most one `if` clause, and contains no other comprehension.
- [SP203](reference.md#sp203) `single-target-assignment`: Assignment: `total = 0`, `x, y = point`. *Condition:* An assignment has exactly one target, before a single `=`. Chained assignment such as `a = b = 0` is not permitted. Unpacking into one tuple target such as `x, y = point` is permitted.
- [SP405](reference.md#sp405) `function-decorator-allowlist`: Decorators on a function or method: `@property`. *Condition:* Each decorator on a function is one of: `@property`, `@<name>.setter` or `@<name>.deleter` for a property defined in the same class, `@staticmethod`, `@classmethod`, or `@override` (imported from `typing`, or written as `@typing.override`). No other decorator is permitted.
- [SP406](reference.md#sp406) `forwarding-varargs`: A variadic positional parameter: `def f(*args)`. *Condition:* A function may declare `*args` only if its body uses `args` only as `*args` in one call, passing the values on unchanged.
- [SP407](reference.md#sp407) `forwarding-kwargs`: A variadic keyword parameter: `def f(**kwargs)`. *Condition:* A function may declare `**kwargs` only if its body uses `kwargs` only as `**kwargs` in one call, passing the values on unchanged.
- [SP408](reference.md#sp408) `nested-functions-without-closures`: A function defined inside the body of another function. *Condition:* A function body may contain a nested `def` only if the nested function does not use any name that is a parameter or a local variable of the enclosing function.
- [SP503](reference.md#sp503) `single-base-class`: The base classes listed in a class header: `class Child(Parent)`. *Condition:* A class lists at most one base class.
- [SP504](reference.md#sp504) `class-decorator-allowlist`: Decorators on a class: `@dataclass`. *Condition:* The only permitted class decorator is `@dataclass` or `@dataclasses.dataclass`, written with or without keyword arguments, such as `@dataclass(frozen=True)`.
- [SP603](reference.md#sp603) `shallow-relative-imports`: Relative imports: `from . import sibling`, `from ..package import name`. *Condition:* A relative import has at most one leading dot. Imports from parent packages use the absolute module path.
- [SP702](reference.md#sp702) `typed-except-handlers`: An `except` clause: `except ValueError as error:`. *Condition:* Every `except` clause names the exception type or types it handles. A bare `except:` is not permitted.

## Allowed

No conditions: `names-and-literals`, `expression-contexts`, `attribute-access`, `calls`, `subscripts-and-slices`, `container-displays`, `arithmetic-operators`, `bitwise-operators`, `boolean-operators`, `comparison-operators`, `f-strings`, `module`, `expression-statements`, `annotated-assignment`, `augmented-assignment`, `delete-statement`, `pass-statement`, `if-statement`, `loops`, `break-and-continue`, `with-statement`, `match-statement`, `function-definitions`, `keyword-arguments`, `yield`, `yield-from`, `class-definitions`, `explicit-imports`, `try-statement`, `raise-statement`, `assert-statement`, `type-alias-statement`, `type-parameters`, `optional-annotations`, `optional-return-annotations`.

Anything not named above is classified by the same registry; look it up in [reference.md](reference.md) rather than guessing.

## Reference and examples

- [reference.md](reference.md): every rule with rationale and compliant and violating examples. Rules link to anchors such as `reference.md#sp601`.
- [examples/before.py](examples/before.py) and [examples/after.py](examples/after.py): the same program in full Python (breaking SP118, SP208, SP304 and SP601 on purpose) and rewritten in the subset. They print the same output.
