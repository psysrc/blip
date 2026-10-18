# Static Errors

These programs are all rejected before they run. Blip is fully type-inferred, so every value has a type whether or not the
source mentions one, and a program whose types cannot be worked out is an error in the program rather than a surprise at
execution time. Each one below is wrong whatever input it is given, which is what makes it a *static* error.

A program that cannot compile has a `#### Error` section recording the error it raises, in place of the `#### Blip IR` and
`#### Execution` sections that a working program has. Beneath the error class is the diagnostic `blip` prints for it, caret and
all, which the test suite checks exactly - so what is shown below is what you will actually see.

For the errors that are *not* static - a decomposition that does not match, an index out of bounds, a directive given the wrong
number of strings - see [Basic Programs](basic_programs.md) and [Input/Output Directives](input_output_directives.md).

## Reassignment Type Change

Variables are monomorphic: a name has one type for its whole life, so it cannot be reassigned to a value of another type.

This is what makes the planned C and C++ backends tractable. If a Blip variable could change type, every target-language
variable would need a tagged union and a check at every use.

#### Blip code

```blip
x = "a"
x = 1

ret x
```

#### Error

```text
SemanticError
<stdin>:2:5: semantic error: cannot assign to 'x': expected 'string', found 'integer'
  |
2 | x = 1
  |     ^
<stdin>:1:1: note: 'x' was bound as 'string' here
  |
1 | x = "a"
  | ^
```

## Type Mismatch

Only strings can be concatenated, so putting an integer beside one is an error.

#### Blip code

```blip
count = 5
message = "you have " count

ret message
```

#### Error

```text
SemanticError
<stdin>:2:23: semantic error: only strings can be concatenated: expected 'string', found 'integer'
  |
2 | message = "you have " count
  |                       ^^^^^
<stdin>:1:1: note: 'count' was bound as 'integer' here
  |
1 | count = 5
  | ^^^^^
```

## Unbound Identifier

A name has to be bound before it is used. Nothing in this program ever gives `greeting` a value.

#### Blip code

```blip
ret greeting
```

#### Error

```text
SemanticError
<stdin>:1:5: semantic error: 'greeting' is used but never bound
  |
1 | ret greeting
  |     ^^^^^^^^
```

## Heterogeneous List

A list is homogeneous: every element has the same type. A list mixing strings and integers has no element type.

#### Blip code

```blip
ret ["a", 1]
```

#### Error

```text
SemanticError
<stdin>:1:11: semantic error: every element of a list must have the same type: expected 'string', found 'integer'
  |
1 | ret ["a", 1]
  |           ^
```

## Undetermined Empty List

`[]` is a list of *something*, and the program is what says what. Here nothing ever uses `things`, so its element type is never
determined and the program has no meaning.

Note that an empty list is perfectly valid once something pins it down - `things = []` followed by `ret things` compiles, because
returning it requires a list of strings.

#### Blip code

```blip
things = []

ret "done"
```

#### Error

```text
SemanticError
<stdin>:1:10: semantic error: cannot infer the type of a list: no constraint determines it
  |
1 | things = []
  |          ^^
```

## Ambiguous Decomposition Patterns

Captures and wildcards in a decomposition pattern must be separated by string literals,
otherwise it's ambiguous which part of the string belongs to which capture/wildcard.

#### Blip code

```blip
x = "hello world"
x -> first second

ret first
```

#### Error

```text
SemanticError
<stdin>:2:6: semantic error: ambiguous decomposition pattern: the capture 'first' is followed by the capture 'second'
  |
2 | x -> first second
  |      ^^^^^
<stdin>:2:12: note: the capture 'second' follows it, with nothing in between
  |
2 | x -> first second
  |            ^^^^^^
```

## Duplicate capture names in decomposition pattern

A decomposition pattern captures each name at most once.

`x -> dup "," dup` looks as though it might assert that both halves of the string are equal, but it doesn't, the captures are independent.

Note that this rule only applies to named captures within the same pattern.
Two separate decomposition statements can capture using the same names, just not two instances of the same name within the same pattern.

#### Blip code

```blip
x = "a,b"
x -> dup "," dup

ret dup
```

#### Error

```text
SemanticError
<stdin>:2:14: semantic error: a decomposition pattern cannot capture 'dup' more than once
  |
2 | x -> dup "," dup
  |              ^^^
<stdin>:2:6: note: 'dup' is already captured here
  |
2 | x -> dup "," dup
  |      ^^^
```

## Empty Decomposition Literal

A string literal in a decomposition pattern cannot be empty.

An empty literal matches at every position, so it says nothing about the string. Worse, it slips a pattern past the rule that
captures must be separated: `x -> first "" second` separates the two captures with a literal that cannot tell them apart, so it
would leave `first` empty for every input, while the identical `x -> first second` is rejected outright.

#### Blip code

```blip
x = input[0]
x -> "" rest

ret rest
```

#### Error

```text
SemanticError
<stdin>:2:6: semantic error: a decomposition pattern cannot contain an empty string literal
  |
2 | x -> "" rest
  |      ^^
```

## Non-Boolean Condition

An `if` branches on a boolean, so any other type is a semantic error.

#### Blip code

```blip
if "Sam" {
    ret "Superuser"
}
```

#### Error

```text
SemanticError
<stdin>:1:4: semantic error: an 'if' condition must be a boolean: expected 'boolean', found 'string'
  |
1 | if "Sam" {
  |    ^^^^^
```

## A Capture Used After Its Block

The names a conditional decomposition captures are bound inside the block it guards, and nowhere else.

#### Blip code

```blip
!in 1

email = input[0]

if email -> name "@" domain {
    ret name
}

ret domain
```

#### Error

```text
SemanticError
<stdin>:9:5: semantic error: 'domain' is used but never bound
  |
9 | ret domain
  |     ^^^^^^
```

## A Variable Bound In Only One Branch

A variable has to be bound in every path that reaches its use.

#### Blip code

```blip
flag = true

if flag {
    label = "yes"
}

ret label
```

#### Error

```text
SemanticError
<stdin>:7:5: semantic error: 'label' is used but never bound
  |
7 | ret label
  |     ^^^^^
```

## Branches That Disagree On A Type

Variables are monomorphic, so the branches that bind them have to agree on what type they have.

#### Blip code

```blip
flag = true

if flag {
    label = "yes"
} else {
    label = 0
}

ret label
```

#### Error

```text
SemanticError
<stdin>:6:5: semantic error: 'label' is bound in both branches of this 'if', so the two types must agree: expected 'string', found 'integer'
  |
6 |     label = 0
  |     ^^^^^
<stdin>:4:5: note: 'label' was bound as 'string' here
  |
4 |     label = "yes"
  |     ^^^^^
```
