<!-- GENERATED FILE: do not edit. Regenerate with `python -m simplified_python.reference`; edit the rules in `subset/`. -->

# The Simplified Python Subset

> **Generated file — do not edit.** This reference is generated from the rule registry in `subset/` by `python -m simplified_python.reference`.
> To change a rule, edit the registry and regenerate this file.

> [!WARNING]
> **Experimental pre-release.** The subset is still being defined and is not ready for general use.
> Rule identifiers, statuses, and the registry format may change without notice between rule-set versions,
> and the checker enforces only the banned rules; restricted conditions still rely on human review.

Rule-set version **1**, defining a subset of the **Python 3.14** grammar.

Every program that conforms to the subset is an ordinary Python program with unchanged behaviour. The subset only removes or narrows constructs. Each construct has one of three statuses:

- **allowed**: the construct may be used without conditions.
- **restricted**: the construct may be used only when the stated condition holds.
- **banned**: the construct must not appear. The entry gives the sanctioned alternative.

## Principles

Every restricted or banned rule cites at least one of these principles.

<a id="p1"></a>

### P1 · local-reasoning

The meaning of a piece of code can be worked out from the code on the screen.

*Review cost addressed:* The reviewer has to leave the diff to find out what a name refers to or what a construct does.

<a id="p2"></a>

### P2 · one-obvious-spelling

Each behaviour has one usual way to write it.

*Review cost addressed:* The reviewer has to recognise several equivalent forms and check that each one means what the others mean.

<a id="p3"></a>

### P3 · no-action-at-a-distance

Code changes only the state and behaviour that it visibly names.

*Review cost addressed:* The reviewer cannot see from the changed lines which other code the change affects.

<a id="p4"></a>

### P4 · bounded-reading-cost

Each construct can be read once, from left to right and top to bottom, without unpacking it.

*Review cost addressed:* The reviewer has to unpack a dense construct inside-out, or trace extra control-flow paths, before judging it.

## Rule index

| Rule | Slug | Status |
|---|---|---|
| [SP101](#sp101) | `names-and-literals` | allowed |
| [SP102](#sp102) | `expression-contexts` | allowed |
| [SP103](#sp103) | `attribute-access` | allowed |
| [SP104](#sp104) | `calls` | allowed |
| [SP105](#sp105) | `subscripts-and-slices` | allowed |
| [SP106](#sp106) | `container-displays` | allowed |
| [SP107](#sp107) | `arithmetic-operators` | allowed |
| [SP108](#sp108) | `bitwise-operators` | allowed |
| [SP109](#sp109) | `boolean-operators` | allowed |
| [SP110](#sp110) | `single-comparison` | restricted |
| [SP111](#sp111) | `comparison-operators` | allowed |
| [SP112](#sp112) | `f-strings` | allowed |
| [SP113](#sp113) | `no-template-strings` | banned |
| [SP114](#sp114) | `flat-conditional-expression` | restricted |
| [SP115](#sp115) | `starred-unpacking` | restricted |
| [SP116](#sp116) | `lambda-as-argument` | restricted |
| [SP117](#sp117) | `simple-comprehensions` | restricted |
| [SP118](#sp118) | `no-walrus` | banned |
| [SP201](#sp201) | `module` | allowed |
| [SP202](#sp202) | `expression-statements` | allowed |
| [SP203](#sp203) | `single-target-assignment` | restricted |
| [SP204](#sp204) | `annotated-assignment` | allowed |
| [SP205](#sp205) | `augmented-assignment` | allowed |
| [SP206](#sp206) | `delete-statement` | allowed |
| [SP207](#sp207) | `pass-statement` | allowed |
| [SP208](#sp208) | `no-global-or-nonlocal` | banned |
| [SP301](#sp301) | `if-statement` | allowed |
| [SP302](#sp302) | `loops` | allowed |
| [SP303](#sp303) | `break-and-continue` | allowed |
| [SP304](#sp304) | `no-loop-else` | banned |
| [SP305](#sp305) | `with-statement` | allowed |
| [SP306](#sp306) | `match-statement` | allowed |
| [SP401](#sp401) | `function-definitions` | allowed |
| [SP402](#sp402) | `keyword-arguments` | allowed |
| [SP403](#sp403) | `yield` | allowed |
| [SP404](#sp404) | `yield-from` | allowed |
| [SP405](#sp405) | `function-decorator-allowlist` | restricted |
| [SP406](#sp406) | `forwarding-varargs` | restricted |
| [SP407](#sp407) | `forwarding-kwargs` | restricted |
| [SP408](#sp408) | `nested-functions-without-closures` | restricted |
| [SP501](#sp501) | `class-definitions` | allowed |
| [SP502](#sp502) | `no-class-keywords` | banned |
| [SP503](#sp503) | `single-base-class` | restricted |
| [SP504](#sp504) | `class-decorator-allowlist` | restricted |
| [SP601](#sp601) | `no-star-import` | banned |
| [SP602](#sp602) | `explicit-imports` | allowed |
| [SP603](#sp603) | `shallow-relative-imports` | restricted |
| [SP701](#sp701) | `try-statement` | allowed |
| [SP702](#sp702) | `typed-except-handlers` | restricted |
| [SP703](#sp703) | `no-except-star` | banned |
| [SP704](#sp704) | `raise-statement` | allowed |
| [SP705](#sp705) | `assert-statement` | allowed |
| [SP801](#sp801) | `no-async` | banned |
| [SP802](#sp802) | `no-async-comprehension` | banned |
| [SP901](#sp901) | `type-alias-statement` | allowed |
| [SP902](#sp902) | `type-parameters` | allowed |
| [SP903](#sp903) | `optional-annotations` | allowed |
| [SP904](#sp904) | `optional-return-annotations` | allowed |

## Expressions

<a id="sp101"></a>

### SP101 · names-and-literals

**Status:** allowed

**Construct:** Names and literal constants: `total`, `42`, `"text"`, `None`, `True`, `...`.

**Rationale:** Names and literals are the atoms of every expression. They say exactly what they are.

Compliant:

```python
limit = 10
label = "ready"
enabled = True
```

<a id="sp102"></a>

### SP102 · expression-contexts

**Status:** allowed

**Construct:** Whether a name, attribute, or subscript is read, assigned, or deleted.

**Rationale:** The context is not written separately. It follows from where the expression stands, so it adds nothing for a reader to check. The statements that store and delete are governed by their own rules.

Compliant:

```python
count = 0
print(count)
```

<a id="sp103"></a>

### SP103 · attribute-access

**Status:** allowed

**Construct:** Reading or assigning an attribute: `user.name`.

**Rationale:** Attribute access is explicit about the object it reads from.

Compliant:

```python
name = user.name
```

<a id="sp104"></a>

### SP104 · calls

**Status:** allowed

**Construct:** Calling a function, method, or class: `send(message, retries=3)`.

**Rationale:** A call names what it calls and lists what it passes.

Compliant:

```python
send(message, retries=3)
```

<a id="sp105"></a>

### SP105 · subscripts-and-slices

**Status:** allowed

**Construct:** Indexing and slicing: `items[0]`, `items[1:-1]`, `table[row, column]`.

**Rationale:** Indexing and slicing are explicit about the container and the position.

Compliant:

```python
first = items[0]
middle = items[1:-1]
```

<a id="sp106"></a>

### SP106 · container-displays

**Status:** allowed

**Construct:** List, tuple, dict, and set displays: `[a, b]`, `(a, b)`, `{"k": v}`, `{a, b}`.

**Rationale:** A display shows every element it builds.

Compliant:

```python
point = (x, y)
names = ["ada", "grace"]
ages = {"ada": 36}
tags = {"new", "sale"}
```

<a id="sp107"></a>

### SP107 · arithmetic-operators

**Status:** allowed

**Construct:** Arithmetic and unary sign operators: `+`, `-`, `*`, `/`, `//`, `%`, `**`, `@`, unary `+` and `-`.

**Rationale:** Arithmetic reads as it does in mathematics, and every reader already knows it.

Compliant:

```python
area = width * height
remaining = -(total - used) // 2
```

<a id="sp108"></a>

### SP108 · bitwise-operators

**Status:** allowed

**Construct:** Bitwise operators: `&`, `|`, `^`, `<<`, `>>`, `~`.

**Rationale:** Bitwise operators have one meaning each and appear in flag handling, set algebra, and type unions (`int | None`). They do not hide control flow.

Compliant:

```python
mask = flags & ~READ_ONLY
optional: int | None = None
```

<a id="sp109"></a>

### SP109 · boolean-operators

**Status:** allowed

**Construct:** Boolean operators: `and`, `or`, `not`.

**Rationale:** Boolean operators read as English and have one meaning each.

Compliant:

```python
ready = connected and not paused
```

<a id="sp110"></a>

### SP110 · single-comparison

**Status:** restricted

**Construct:** A comparison: `a < b`, `x == y`, `key in table`.

**Condition:** A comparison uses exactly one comparison operator. Chained comparisons such as `a < b < c` are not permitted.

**Rationale:** One comparison is read at a glance. A chain such as `a < b == c` is an implicit `and` of several comparisons and is easy to misread, in particular when the operators are mixed.

**Principles:** [P2 · one-obvious-spelling](#p2), [P4 · bounded-reading-cost](#p4)

Compliant:

```python
in_range = low <= value and value < high
```

Violating:

```python
in_range = low <= value < high
```

<a id="sp111"></a>

### SP111 · comparison-operators

**Status:** allowed

**Construct:** The comparison operators: `==`, `!=`, `<`, `<=`, `>`, `>=`, `is`, `is not`, `in`, `not in`.

**Rationale:** Each operator has one meaning. How many operators a comparison may use is governed by SP110.

Compliant:

```python
found = key in table
missing = value is None
```

<a id="sp112"></a>

### SP112 · f-strings

**Status:** allowed

**Construct:** Formatted string literals: `f"{name}: {count:>4}"`.

**Rationale:** An f-string shows each value at the place where it appears in the text. It is the one usual way to build a string from values.

Compliant:

```python
line = f"{name}: {count:>4}"
```

<a id="sp113"></a>

### SP113 · no-template-strings

**Status:** banned

**Construct:** Template string literals (PEP 750): `t"Hello {name}"`.

**Rationale:** A template string looks like an f-string but produces a `Template` object, not a `str`. Its meaning depends on the code that later consumes the template. This gives a second spelling close to f-strings, and its effect is decided away from the literal. Template strings are new and most reviewers do not know them yet.

**Principles:** [P2 · one-obvious-spelling](#p2), [P1 · local-reasoning](#p1)

Violating:

```python
greeting = render(t"Hello {name}")
```

**Instead:** Use an f-string to build text. To escape or quote values, call the escaping function explicitly on each value.

Compliant:

```python
greeting = f"Hello {escape(name)}"
```

<a id="sp114"></a>

### SP114 · flat-conditional-expression

**Status:** restricted

**Construct:** A conditional expression: `a if condition else b`.

**Condition:** The test and both branches of a conditional expression do not contain another conditional expression.

**Rationale:** One conditional expression reads as a sentence. Nested conditional expressions must be unpacked to find which branch applies. An `if` statement shows the same logic as visible branches.

**Principles:** [P4 · bounded-reading-cost](#p4)

Compliant:

```python
label = "on" if enabled else "off"
```

Violating:

```python
label = "high" if level > 2 else "mid" if level > 1 else "low"
```

<a id="sp115"></a>

### SP115 · starred-unpacking

**Status:** restricted

**Construct:** Starred expressions: `f(*args)`, `[*head, *tail]`, `first, *rest = items`.

**Condition:** A starred expression may unpack values into a call or a list, tuple, or set display. It must not be an assignment target or a `for` loop target.

**Rationale:** Unpacking into a call or display shows where the values go. A starred target splits a sequence by position, and the reader must count the other targets to know what each name holds. Indexing or slicing says it directly.

**Principles:** [P4 · bounded-reading-cost](#p4)

Compliant:

```python
combined = [*head, *tail]
first = items[0]
rest = items[1:]
```

Violating:

```python
first, *rest = items
```

<a id="sp116"></a>

### SP116 · lambda-as-argument

**Status:** restricted

**Construct:** Anonymous functions: `lambda item: item.size`.

**Condition:** A lambda is permitted only as a direct argument of a call, such as `sorted(items, key=lambda item: item.size)`.

**Rationale:** As a short argument, a lambda keeps a one-line function next to the call that uses it. A lambda stored in a name or a data structure is a function without a name: it cannot be found by searching, cannot be tested directly, and shows no name in tracebacks. Use `def` for it.

**Principles:** [P1 · local-reasoning](#p1)

Compliant:

```python
ordered = sorted(items, key=lambda item: item.size)
```

Violating:

```python
by_size = lambda item: item.size
ordered = sorted(items, key=by_size)
```

<a id="sp117"></a>

### SP117 · simple-comprehensions

**Status:** restricted

**Construct:** List, set, and dict comprehensions, generator expressions, and their `for` / `if` clauses.

**Condition:** A comprehension has exactly one `for` clause and at most one `if` clause, and contains no other comprehension.

**Rationale:** A comprehension with one `for` and one filter reads left to right. With more clauses, or a comprehension inside another, the order of evaluation runs inside-out and the reader must reconstruct the loops. Nested `for` statements show the same logic in the order it runs.

**Principles:** [P4 · bounded-reading-cost](#p4)

Compliant:

```python
names = [user.name for user in users if user.active]
```

Violating:

```python
cells = [cell for row in grid for cell in row if cell]
```

Violating:

```python
totals = {key: sum(v for v in values) for key, values in groups.items()}
```

<a id="sp118"></a>

### SP118 · no-walrus

**Status:** banned

**Construct:** Assignment expressions (the walrus operator): `(match := pattern.search(line))`.

**Rationale:** An assignment expression binds a name in the middle of another expression, where a reader does not expect a binding. It gives a second spelling of assignment, and the binding is easy to overlook when scanning for where a name is set.

**Principles:** [P2 · one-obvious-spelling](#p2), [P3 · no-action-at-a-distance](#p3)

Violating:

```python
if (found := pattern.search(line)):
    handle(found)
```

**Instead:** Assign the value in its own statement on the line before, then use the name.

Compliant:

```python
found = pattern.search(line)
if found:
    handle(found)
```

## Statements

<a id="sp201"></a>

### SP201 · module

**Status:** allowed

**Construct:** A source file: the module that holds its top-level statements.

**Rationale:** Every file is a module. The rules for its contents apply to the statements it holds.

Compliant:

```python
VERSION = "1.0"
```

<a id="sp202"></a>

### SP202 · expression-statements

**Status:** allowed

**Construct:** An expression used as a statement, usually a call whose result is not kept: `log.info("done")`.

**Rationale:** Calling a function for its effect is ordinary, and docstrings are expression statements.

Compliant:

```python
log.info("done")
```

<a id="sp203"></a>

### SP203 · single-target-assignment

**Status:** restricted

**Construct:** Assignment: `total = 0`, `x, y = point`.

**Condition:** An assignment has exactly one target, before a single `=`. Chained assignment such as `a = b = 0` is not permitted. Unpacking into one tuple target such as `x, y = point` is permitted.

**Rationale:** With chained assignment, several names refer to the same object. If the object is mutable, a change through one name appears through the other. One target per statement makes each binding explicit.

**Principles:** [P2 · one-obvious-spelling](#p2), [P3 · no-action-at-a-distance](#p3)

Compliant:

```python
low = 0
high = 0
x, y = point
```

Violating:

```python
low = high = 0
```

<a id="sp204"></a>

### SP204 · annotated-assignment

**Status:** allowed

**Construct:** Assignment with a type annotation: `count: int = 0`.

**Rationale:** An annotated assignment is an ordinary assignment that also states the type.

Compliant:

```python
count: int = 0
```

<a id="sp205"></a>

### SP205 · augmented-assignment

**Status:** allowed

**Construct:** Augmented assignment: `total += amount`.

**Rationale:** Augmented assignment is a familiar shorthand that names its target once.

Compliant:

```python
total += amount
```

<a id="sp206"></a>

### SP206 · delete-statement

**Status:** allowed

**Construct:** The `del` statement: `del cache[key]`.

**Rationale:** `del` names exactly the name, item, or attribute it removes.

Compliant:

```python
del cache[key]
```

<a id="sp207"></a>

### SP207 · pass-statement

**Status:** allowed

**Construct:** The `pass` statement.

**Rationale:** `pass` marks an intentionally empty block and does nothing else.

Compliant:

```python
class Empty:
    pass
```

<a id="sp208"></a>

### SP208 · no-global-or-nonlocal

**Status:** banned

**Construct:** The `global` and `nonlocal` declarations.

**Rationale:** `global` and `nonlocal` let a function rebind a name that belongs to another scope. A reader of the module or of the outer function cannot see from that code that the name is changed somewhere else.

**Principles:** [P3 · no-action-at-a-distance](#p3)

Violating:

```python
def increment():
    global count
    count += 1
```

Violating:

```python
def counter():
    count = 0
    def step():
        nonlocal count
        count += 1
    return step
```

**Instead:** Pass the value in as an argument and return the new value. To keep shared state, put it in an object that is passed explicitly.

Compliant:

```python
def increment(count):
    return count + 1

count = increment(count)
```

## Control flow

<a id="sp301"></a>

### SP301 · if-statement

**Status:** allowed

**Construct:** The `if` / `elif` / `else` statement.

**Rationale:** Branches are visible and read top to bottom.

Compliant:

```python
if size > LIMIT:
    reject()
elif size == 0:
    skip()
else:
    accept()
```

<a id="sp302"></a>

### SP302 · loops

**Status:** allowed

**Construct:** The `for` and `while` loops.

**Rationale:** Loops show what they repeat and when they stop. The `else` clause of a loop is governed by SP304.

Compliant:

```python
for item in items:
    process(item)

while queue:
    process(queue.pop())
```

<a id="sp303"></a>

### SP303 · break-and-continue

**Status:** allowed

**Construct:** The `break` and `continue` statements.

**Rationale:** `break` and `continue` act on the innermost loop, which is visible around them.

Compliant:

```python
for line in lines:
    if not line:
        continue
    if line == "END":
        break
    handle(line)
```

<a id="sp304"></a>

### SP304 · no-loop-else

**Status:** banned

**Construct:** An `else` clause on a `for` or `while` loop.

**Rationale:** The `else` of a loop runs when the loop ends without `break`. Many readers expect the opposite, or expect it to run when the loop body never ran. The meaning depends on knowing a rarely used rule.

**Principles:** [P4 · bounded-reading-cost](#p4), [P2 · one-obvious-spelling](#p2)

Violating:

```python
for item in items:
    if item.matches(query):
        break
else:
    report_missing(query)
```

**Instead:** Record the outcome in a variable inside the loop, then test that variable after the loop with an `if` statement.

Compliant:

```python
found = None
for item in items:
    if item.matches(query):
        found = item
        break
if found is None:
    report_missing(query)
```

<a id="sp305"></a>

### SP305 · with-statement

**Status:** allowed

**Construct:** The `with` statement and each of its context managers: `with open(path) as handle:`.

**Rationale:** `with` shows where a resource is acquired and where it is released.

Compliant:

```python
with open(path) as handle:
    data = handle.read()
```

<a id="sp306"></a>

### SP306 · match-statement

**Status:** allowed

**Construct:** The `match` statement, its `case` clauses, and every pattern form.

**Rationale:** `match` lists the cases flat, one after another, and states the shape of the data each case accepts. This is easier to review than a chain of `isinstance` checks and index lookups.

Compliant:

```python
match command:
    case ["move", x, y]:
        move(x, y)
    case {"action": "stop"} | None:
        stop()
    case Point(x=0, y=0):
        reset()
    case [first, *others] if others:
        batch(first, others)
    case other:
        log(other)
```

## Functions

<a id="sp401"></a>

### SP401 · function-definitions

**Status:** allowed

**Construct:** Function definitions with `def`, their parameter lists and parameters, and `return`.

**Rationale:** A named function with an explicit parameter list is the basic unit of review. Decorators, variadic parameters, and nested definitions are governed by SP405 to SP408.

Compliant:

```python
def scale(value, factor=2, *, clamp=False):
    result = value * factor
    return min(result, LIMIT) if clamp else result
```

<a id="sp402"></a>

### SP402 · keyword-arguments

**Status:** allowed

**Construct:** Keyword arguments in a call: `connect(host, timeout=5)`.

**Rationale:** A keyword argument names the parameter it sets, so the call explains itself.

Compliant:

```python
connect(host, timeout=5)
```

<a id="sp403"></a>

### SP403 · yield

**Status:** allowed

**Construct:** The `yield` expression, which makes a function a generator.

**Rationale:** A generator produces values one at a time in plain sequential code. Each `yield` marks a point where a value is produced.

Compliant:

```python
def chunks(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]
```

<a id="sp404"></a>

### SP404 · yield-from

**Status:** allowed

**Construct:** The `yield from` expression, which passes on every value of another iterable.

**Rationale:** `yield from` names the iterable it delegates to. It replaces a loop that yields each item and does not hide where the values come from. Its separate use for generator-based coroutines is outside this subset, because async code is not yet permitted (SP801).

Compliant:

```python
def walk(tree):
    yield tree.value
    for child in tree.children:
        yield from walk(child)
```

<a id="sp405"></a>

### SP405 · function-decorator-allowlist

**Status:** restricted

**Construct:** Decorators on a function or method: `@property`.

**Condition:** Each decorator on a function is one of: `@property`, `@<name>.setter` or `@<name>.deleter` for a property defined in the same class, `@staticmethod`, `@classmethod`, or `@override` (imported from `typing`, or written as `@typing.override`). No other decorator is permitted.

**Rationale:** A decorator can replace the function under it with anything. The reader sees one definition, but a different object runs. The allowlist keeps the decorators whose effect every Python reader knows. A name-based allowlist cannot prove that the name refers to the standard-library object, so the names on the list must not be rebound.

**Principles:** [P1 · local-reasoning](#p1), [P3 · no-action-at-a-distance](#p3)

Compliant:

```python
class Account:
    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        self._balance = value

    @classmethod
    def empty(cls):
        return cls(0)
```

Violating:

```python
@retry(times=3)
def fetch(url):
    return download(url)
```

<a id="sp406"></a>

### SP406 · forwarding-varargs

**Status:** restricted

**Construct:** A variadic positional parameter: `def f(*args)`.

**Condition:** A function may declare `*args` only if its body uses `args` only as `*args` in one call, passing the values on unchanged.

**Rationale:** `*args` hides the parameters a function takes. The reader must find every caller to learn what is passed. Forwarding to one call is the one use where the target function documents the real parameters.

**Principles:** [P1 · local-reasoning](#p1)

Compliant:

```python
def logged(message, *args):
    return log.info(message, *args)
```

Violating:

```python
def area(*args):
    return args[0] * args[1]
```

<a id="sp407"></a>

### SP407 · forwarding-kwargs

**Status:** restricted

**Construct:** A variadic keyword parameter: `def f(**kwargs)`.

**Condition:** A function may declare `**kwargs` only if its body uses `kwargs` only as `**kwargs` in one call, passing the values on unchanged.

**Rationale:** `**kwargs` hides which options a function accepts. Lookups such as `kwargs.get("timeout")` scatter the real parameter list through the body. Forwarding to one call is the one use where the target function documents the real parameters.

**Principles:** [P1 · local-reasoning](#p1)

Compliant:

```python
def make_client(url, **kwargs):
    return Client(url, **kwargs)
```

Violating:

```python
def connect(**kwargs):
    timeout = kwargs.get("timeout", 5)
    return open_socket(kwargs["host"], timeout)
```

<a id="sp408"></a>

### SP408 · nested-functions-without-closures

**Status:** restricted

**Construct:** A function defined inside the body of another function.

**Condition:** A function body may contain a nested `def` only if the nested function does not use any name that is a parameter or a local variable of the enclosing function.

**Rationale:** A nested function that captures names from its enclosing function is a closure. Its behaviour depends on state that is not in its parameter list, and that state can change after the closure is created. A nested function that captures nothing is a local helper. Its inputs are visible.

**Principles:** [P1 · local-reasoning](#p1), [P3 · no-action-at-a-distance](#p3)

Compliant:

```python
def total_size(paths):
    def size_of(path):
        return path.stat().st_size

    return sum(size_of(path) for path in paths)
```

Violating:

```python
def make_scaler(factor):
    def scale(value):
        return value * factor

    return scale
```

## Classes

<a id="sp501"></a>

### SP501 · class-definitions

**Status:** allowed

**Construct:** Class definitions with `class`.

**Rationale:** A class groups data with the methods that act on it, under one name. Base lists, class keywords, and class decorators are governed by SP502 to SP504.

Compliant:

```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

<a id="sp502"></a>

### SP502 · no-class-keywords

**Status:** banned

**Construct:** Keyword arguments in a class header: `class A(metaclass=Meta)`, `class B(Base, flag=True)`.

**Rationale:** Class keywords select a metaclass or pass arguments to an `__init_subclass__` hook. Either can change how the class is built, but the code that does this is somewhere else. The reader of the class body cannot see what runs when the class is defined.

**Principles:** [P1 · local-reasoning](#p1), [P3 · no-action-at-a-distance](#p3)

Violating:

```python
class Plugin(Base, metaclass=Registered):
    name = "csv"
```

**Instead:** Write the behaviour as explicit methods or as module-level functions. To check subclasses, call a check function explicitly after the class is defined.

Compliant:

```python
class Plugin(Base):
    name = "csv"


register(Plugin)
```

<a id="sp503"></a>

### SP503 · single-base-class

**Status:** restricted

**Construct:** The base classes listed in a class header: `class Child(Parent)`.

**Condition:** A class lists at most one base class.

**Rationale:** With multiple inheritance, the method that runs depends on the method resolution order across every base class and their bases. To answer the question "what does this call do?", the reader must read code outside the class.

**Principles:** [P1 · local-reasoning](#p1)

Compliant:

```python
class Admin(User):
    pass
```

Violating:

```python
class Admin(User, AuditMixin):
    pass
```

<a id="sp504"></a>

### SP504 · class-decorator-allowlist

**Status:** restricted

**Construct:** Decorators on a class: `@dataclass`.

**Condition:** The only permitted class decorator is `@dataclass` or `@dataclasses.dataclass`, written with or without keyword arguments, such as `@dataclass(frozen=True)`.

**Rationale:** A class decorator can replace or change the class under it. Dataclasses are the standard way to declare a record type, and every Python reader knows what they generate. Other class decorators register, wrap, or rewrite the class away from its definition.

**Principles:** [P1 · local-reasoning](#p1), [P3 · no-action-at-a-distance](#p3)

Compliant:

```python
@dataclass(frozen=True)
class Point:
    x: int
    y: int
```

Violating:

```python
@register("csv")
class CsvReader:
    pass
```

## Imports

<a id="sp601"></a>

### SP601 · no-star-import

**Status:** banned

**Construct:** Importing every public name from a module with `from module import *`.

**Rationale:** A star import binds names that do not appear anywhere in the importing file. A reader who meets an unfamiliar name cannot tell which module it came from, and a later change to the imported module can silently add or shadow names.

**Principles:** [P1 · local-reasoning](#p1), [P3 · no-action-at-a-distance](#p3)

Violating:

```python
from os.path import *

stem, suffix = splitext(join("build", "out.txt"))
```

**Instead:** Import the names you use explicitly, or import the module and qualify each name.

Compliant:

```python
from os.path import join, splitext

stem, suffix = splitext(join("build", "out.txt"))
```

<a id="sp602"></a>

### SP602 · explicit-imports

**Status:** allowed

**Construct:** `import module`, `from module import name`, and `as` aliases.

**Rationale:** An explicit import says where each name comes from, at the top of the file. Star imports and relative-import depth are governed by SP601 and SP603.

Compliant:

```python
import json
from pathlib import Path
from collections import defaultdict as multimap
```

<a id="sp603"></a>

### SP603 · shallow-relative-imports

**Status:** restricted

**Construct:** Relative imports: `from . import sibling`, `from ..package import name`.

**Condition:** A relative import has at most one leading dot. Imports from parent packages use the absolute module path.

**Rationale:** One dot means "this package", and the reader can see that in the file tree. Each extra dot makes the reader count directories to find the module, and the import breaks silently when the file moves.

**Principles:** [P1 · local-reasoning](#p1)

Compliant:

```python
from . import models
from .models import User
from myapp.core import settings
```

Violating:

```python
from ..core import settings
```

## Exceptions

<a id="sp701"></a>

### SP701 · try-statement

**Status:** allowed

**Construct:** The `try` statement with `except`, `else`, and `finally` clauses.

**Rationale:** `try` shows which code may fail and where the failure is handled. The handlers are governed by SP702.

Compliant:

```python
try:
    config = load(path)
except FileNotFoundError:
    config = DEFAULTS
finally:
    close_log()
```

<a id="sp702"></a>

### SP702 · typed-except-handlers

**Status:** restricted

**Construct:** An `except` clause: `except ValueError as error:`.

**Condition:** Every `except` clause names the exception type or types it handles. A bare `except:` is not permitted.

**Rationale:** A bare `except:` also catches `KeyboardInterrupt` and `SystemExit`, and it does not tell the reader which failure is expected. A named exception type states what the handler is for.

**Principles:** [P1 · local-reasoning](#p1)

Compliant:

```python
try:
    value = int(text)
except ValueError as error:
    report(error)
```

Violating:

```python
try:
    value = int(text)
except:
    value = 0
```

<a id="sp703"></a>

### SP703 · no-except-star

**Status:** banned

**Construct:** The `try` statement with `except*` clauses for exception groups.

**Rationale:** With `except*`, several handlers can run for one exception group, and each handler sees only part of the group. This doubles the control-flow paths the reader must trace. Exception groups come from concurrent code, which is not yet in the subset.

**Principles:** [P4 · bounded-reading-cost](#p4)

Violating:

```python
try:
    run_all(tasks)
except* ValueError as group:
    report(group)
```

**Instead:** Catch the `ExceptionGroup` with a normal `except` clause and inspect its `exceptions` attribute explicitly.

Compliant:

```python
try:
    run_all(tasks)
except ExceptionGroup as group:
    for error in group.exceptions:
        report(error)
```

<a id="sp704"></a>

### SP704 · raise-statement

**Status:** allowed

**Construct:** The `raise` statement, including `raise ... from ...`.

**Rationale:** `raise` states which failure occurs and, with `from`, what caused it.

Compliant:

```python
raise ConfigError(path) from error
```

<a id="sp705"></a>

### SP705 · assert-statement

**Status:** allowed

**Construct:** The `assert` statement.

**Rationale:** `assert` states an invariant at the place where the code depends on it.

Compliant:

```python
assert count >= 0, "count must not be negative"
```

## Asynchronous code

<a id="sp801"></a>

### SP801 · no-async

**Status:** banned

**Construct:** Coroutines and asynchronous statements: `async def`, `await`, `async for`, `async with`.

**Rationale:** Every `await` is a point where other code can run and change shared state. To review it, the reader must consider every interleaving, and this code is not visible in the function being read. The subset does not yet define rules that keep that cost bounded, so async syntax is excluded for now.

**Principles:** [P3 · no-action-at-a-distance](#p3), [P4 · bounded-reading-cost](#p4)

Violating:

```python
async def fetch_all(session, urls):
    async with session:
        return [await session.get(url) for url in urls]
```

Violating:

```python
async def drain(stream):
    async for chunk in stream:
        consume(chunk)
```

**Instead:** Write synchronous code. If concurrency is necessary, keep it outside code that must conform to the subset until async rules exist.

Compliant:

```python
def fetch_all(urls):
    return [download(url) for url in urls]
```

<a id="sp802"></a>

### SP802 · no-async-comprehension

**Status:** banned

**Construct:** An `async for` clause in a comprehension: `[x async for x in stream]`.

**Rationale:** An asynchronous comprehension is async code in expression form, so the reasoning of SP801 applies to it.

**Principles:** [P3 · no-action-at-a-distance](#p3), [P4 · bounded-reading-cost](#p4)

Violating:

```python
async def collect(stream):
    return [chunk async for chunk in stream]
```

**Instead:** Write synchronous code; see SP801.

Compliant:

```python
chunks = [chunk for chunk in stream]
```

## Typing

<a id="sp901"></a>

### SP901 · type-alias-statement

**Status:** allowed

**Construct:** The `type` statement, which declares a type alias: `type Pair = tuple[int, int]`.

**Rationale:** A `type` statement gives a type a name, at one visible place.

Compliant:

```python
type Pair = tuple[int, int]
```

<a id="sp902"></a>

### SP902 · type-parameters

**Status:** allowed

**Construct:** Type parameters in brackets after a function, class, or alias name: `[T]`, `[**P]`, `[*Ts]`.

**Rationale:** Inline type parameters are declared where they are used, and their scope is the definition that declares them. Module-level `TypeVar(...)` objects, which these replace, are visible across the whole module.

Compliant:

```python
def first[T](items: list[T]) -> T:
    return items[0]


class Registry[K, V]:
    pass


type Callback[**P] = Callable[P, None]
type Row[*Ts] = tuple[*Ts]
```

<a id="sp903"></a>

### SP903 · optional-annotations

**Status:** allowed

**Construct:** Type annotations on parameters and on assignments: `def f(count: int)`, `total: float = 0.0`.

**Rationale:** Annotations state the expected type at the place of use, and type checkers can verify them. They are permitted but not required. A rule that requires them would be a rule about a construct that is absent, and the anchor model cannot express that. A later change may add it.

Compliant:

```python
def repeat(text: str, count: int) -> str:
    total: int = len(text) * count
    return text * count
```

<a id="sp904"></a>

### SP904 · optional-return-annotations

**Status:** allowed

**Construct:** A return annotation on a function: `def f() -> int`.

**Rationale:** A return annotation states what the function produces. It is permitted but not required, for the reason given in SP903.

Compliant:

```python
def count_words(text) -> int:
    return len(text.split())
```
