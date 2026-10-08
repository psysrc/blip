# Static Errors

These programs are all rejected before they run. Blip is fully type-inferred, so every value has a type whether or not the
source mentions one, and a program whose types cannot be worked out is an error in the program rather than a surprise at
execution time. Each one below is wrong whatever input it is given, which is what makes it a *static* error.

A program that cannot compile has a `#### Compilation` section recording the error it raises, in place of the `#### Blip IR` and
`#### Execution` sections that a working program has.

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

#### Compilation

```text
SemanticError
```

## Type Mismatch

Only strings can be concatenated, so putting an integer beside one is an error.

#### Blip code

```blip
count = 5
message = "you have " count

ret message
```

#### Compilation

```text
SemanticError
```

## Unbound Identifier

A name has to be bound before it is used. Nothing in this program ever gives `greeting` a value.

#### Blip code

```blip
ret greeting
```

#### Compilation

```text
SemanticError
```

## Non-String Decomposition Target

Decomposition takes a string apart, so only a string can be decomposed.

#### Blip code

```blip
count = 5
count -> first "," second

ret first
```

#### Compilation

```text
SemanticError
```

## Heterogeneous List

A list is homogeneous: every element has the same type. A list mixing strings and integers has no element type.

#### Blip code

```blip
ret ["a", 1]
```

#### Compilation

```text
SemanticError
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

#### Compilation

```text
SemanticError
```
