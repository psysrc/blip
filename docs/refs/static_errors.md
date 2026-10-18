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
