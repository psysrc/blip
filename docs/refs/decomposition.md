# Decomposition

Decomposition is at the heart of Blip. It allows you to decompose a string into substrings and assert the string's pattern.

Decomposition patterns are not a search. Every character of the target has to be accounted for by some element of the pattern, so a literal
at the start of a pattern has to start the string, a literal at the end has to end it, and any text not captured by the pattern makes
the decomposition fail.

## Patterns Match The Whole String

This pattern asserts that the string is wrapped in angle brackets. `"<"` has to start the string and `">"` has to end it.

Note that a capture is allowed to match the empty string, which is how `"<>"` decomposes into an empty name.

#### Blip code

```blip
tag = input[0]
tag -> "<" name ">"

ret name
```

#### Blip IR

<details>
<summary><i>Expand...</i></summary>

```json
{
    "type": "program",
    "statements": [
        {
            "type": "assignment",
            "identifier": {
                "type": "identifier",
                "blip_type": "string",
                "name": "tag"
            },
            "expression": {
                "type": "index",
                "blip_type": "string",
                "identifier": {
                    "type": "identifier",
                    "blip_type": "list[string]",
                    "name": "input"
                },
                "index": {
                    "type": "integer_literal",
                    "blip_type": "integer",
                    "value": 0
                }
            }
        },
        {
            "type": "decomposition",
            "identifier": {
                "type": "identifier",
                "blip_type": "string",
                "name": "tag"
            },
            "pattern": [
                {
                    "type": "string_literal",
                    "blip_type": "string",
                    "value": "<"
                },
                {
                    "type": "identifier",
                    "blip_type": "string",
                    "name": "name"
                },
                {
                    "type": "string_literal",
                    "blip_type": "string",
                    "value": ">"
                }
            ]
        },
        {
            "type": "return",
            "expression": {
                "type": "identifier",
                "blip_type": "string",
                "name": "name"
            }
        }
    ]
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`["<hello>"]`|`["hello"]`|
|`["<>"]`|`[""]`|
|`["prefix<hello>"]`|`Error`|
|`["<hello>suffix"]`|`Error`|
|`["hello"]`|`Error`|

## Wildcards Account For The Rest

A wildcard is how a pattern says "I don't care what is here". This program asks only whether the string contains a `b`
somewhere, so it needs a wildcard on each side to cover whatever surrounds it.

Without them the pattern would be `x -> "b"`, which asks whether the string *is* `b` - a very different question.

#### Blip code

```blip
x = input[0]
x -> * "b" *

ret "found"
```

#### Blip IR

<details>
<summary><i>Expand...</i></summary>

```json
{
    "type": "program",
    "statements": [
        {
            "type": "assignment",
            "identifier": {
                "type": "identifier",
                "blip_type": "string",
                "name": "x"
            },
            "expression": {
                "type": "index",
                "blip_type": "string",
                "identifier": {
                    "type": "identifier",
                    "blip_type": "list[string]",
                    "name": "input"
                },
                "index": {
                    "type": "integer_literal",
                    "blip_type": "integer",
                    "value": 0
                }
            }
        },
        {
            "type": "decomposition",
            "identifier": {
                "type": "identifier",
                "blip_type": "string",
                "name": "x"
            },
            "pattern": [
                {
                    "type": "decomposition_wildcard"
                },
                {
                    "type": "string_literal",
                    "blip_type": "string",
                    "value": "b"
                },
                {
                    "type": "decomposition_wildcard"
                }
            ]
        },
        {
            "type": "return",
            "expression": {
                "type": "string_literal",
                "blip_type": "string",
                "value": "found"
            }
        }
    ]
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`["abc"]`|`["found"]`|
|`["b"]`|`["found"]`|
|`["bbb"]`|`["found"]`|
|`["ac"]`|`Error`|
|`[""]`|`Error`|

## Captures Are Lazy

A capture runs up to the *first* following occurrence of the literal after it.

#### Blip code

```blip
dotted = input[0]
dotted -> head "." tail

ret [head, tail]
```

#### Blip IR

<details>
<summary><i>Expand...</i></summary>

```json
{
    "type": "program",
    "statements": [
        {
            "type": "assignment",
            "identifier": {
                "type": "identifier",
                "blip_type": "string",
                "name": "dotted"
            },
            "expression": {
                "type": "index",
                "blip_type": "string",
                "identifier": {
                    "type": "identifier",
                    "blip_type": "list[string]",
                    "name": "input"
                },
                "index": {
                    "type": "integer_literal",
                    "blip_type": "integer",
                    "value": 0
                }
            }
        },
        {
            "type": "decomposition",
            "identifier": {
                "type": "identifier",
                "blip_type": "string",
                "name": "dotted"
            },
            "pattern": [
                {
                    "type": "identifier",
                    "blip_type": "string",
                    "name": "head"
                },
                {
                    "type": "string_literal",
                    "blip_type": "string",
                    "value": "."
                },
                {
                    "type": "identifier",
                    "blip_type": "string",
                    "name": "tail"
                }
            ]
        },
        {
            "type": "return",
            "expression": {
                "type": "list",
                "blip_type": "list[string]",
                "elements": [
                    {
                        "type": "identifier",
                        "blip_type": "string",
                        "name": "head"
                    },
                    {
                        "type": "identifier",
                        "blip_type": "string",
                        "name": "tail"
                    }
                ]
            }
        }
    ]
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`["a.b.c"]`|`["a", "b.c"]`|
|`["one.two.three.four"]`|`["one", "two.three.four"]`|
|`["a.b"]`|`["a", "b"]`|
|`["no dot"]`|`Error`|

## Backtracking

A capture runs up to the *first* following occurrence of the literal after it.
However, if after that the pattern doesn't match, the decomposition
can backtrack and try the *next* occurrence of the literal and check the pattern again.
This is because the decomposition pattern must match the entire string, not a subset of it.

Here `archive.gz.gz` can match with `stem == "archive.gz"`, but by stopping at the first `.gz` it would leave a trailing `.gz`, failing
the pattern. So, the decomposition tries the next occurrence of `.gz` and tries again.

#### Blip code

```blip
file = input[0]
file -> stem ".gz"

ret stem
```

#### Blip IR

<details>
<summary><i>Expand...</i></summary>

```json
{
    "type": "program",
    "statements": [
        {
            "type": "assignment",
            "identifier": {
                "type": "identifier",
                "blip_type": "string",
                "name": "file"
            },
            "expression": {
                "type": "index",
                "blip_type": "string",
                "identifier": {
                    "type": "identifier",
                    "blip_type": "list[string]",
                    "name": "input"
                },
                "index": {
                    "type": "integer_literal",
                    "blip_type": "integer",
                    "value": 0
                }
            }
        },
        {
            "type": "decomposition",
            "identifier": {
                "type": "identifier",
                "blip_type": "string",
                "name": "file"
            },
            "pattern": [
                {
                    "type": "identifier",
                    "blip_type": "string",
                    "name": "stem"
                },
                {
                    "type": "string_literal",
                    "blip_type": "string",
                    "value": ".gz"
                }
            ]
        },
        {
            "type": "return",
            "expression": {
                "type": "identifier",
                "blip_type": "string",
                "name": "stem"
            }
        }
    ]
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`["archive.gz"]`|`["archive"]`|
|`["archive.gz.gz"]`|`["archive.gz"]`|
|`["archive"]`|`Error`|
|`["archive.gz.tar"]`|`Error`|

## Literals Are Text, Not Patterns

A string literal in a pattern matches itself and nothing else. Characters that mean something in a regular expression
have no special meaning in Blip, so this program asks whether the string contains a full stop - not whether it contains any
character at all.

#### Blip code

```blip
x = input[0]
x -> * "." *

ret "found"
```

#### Blip IR

<details>
<summary><i>Expand...</i></summary>

```json
{
    "type": "program",
    "statements": [
        {
            "type": "assignment",
            "identifier": {
                "type": "identifier",
                "blip_type": "string",
                "name": "x"
            },
            "expression": {
                "type": "index",
                "blip_type": "string",
                "identifier": {
                    "type": "identifier",
                    "blip_type": "list[string]",
                    "name": "input"
                },
                "index": {
                    "type": "integer_literal",
                    "blip_type": "integer",
                    "value": 0
                }
            }
        },
        {
            "type": "decomposition",
            "identifier": {
                "type": "identifier",
                "blip_type": "string",
                "name": "x"
            },
            "pattern": [
                {
                    "type": "decomposition_wildcard"
                },
                {
                    "type": "string_literal",
                    "blip_type": "string",
                    "value": "."
                },
                {
                    "type": "decomposition_wildcard"
                }
            ]
        },
        {
            "type": "return",
            "expression": {
                "type": "string_literal",
                "blip_type": "string",
                "value": "found"
            }
        }
    ]
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`["a.b"]`|`["found"]`|
|`["."]`|`["found"]`|
|`["abc"]`|`Error`|
|`[""]`|`Error`|

## Non-String Decomposition Target

Only strings can be decomposed.

#### Blip code

```blip
count = 5
count -> first "," second

ret first
```

#### Error

```text
SemanticError
<stdin>:2:1: semantic error: only strings can be decomposed: expected 'string', found 'integer'
  |
2 | count -> first "," second
  | ^^^^^
<stdin>:1:1: note: 'count' was bound as 'integer' here
  |
1 | count = 5
  | ^^^^^
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

## Conditional Decomposition With An Else

An `else` block runs when the decomposition fails.

#### Blip code

```blip
!in 1
!out 1

data = input[0]

if data -> "[" num "]" {
    ret "found number: " num
} else {
    ret "not a bracketed number"
}
```

#### Blip IR

<details>
<summary><i>Expand...</i></summary>

```json
{
    "type": "program",
    "statements": [
        {
            "type": "assignment",
            "identifier": {
                "type": "identifier",
                "blip_type": "string",
                "name": "data"
            },
            "expression": {
                "type": "index",
                "blip_type": "string",
                "identifier": {
                    "type": "identifier",
                    "blip_type": "list[string]",
                    "name": "input"
                },
                "index": {
                    "type": "integer_literal",
                    "blip_type": "integer",
                    "value": 0
                }
            }
        },
        {
            "type": "if",
            "condition": {
                "type": "decomposition_test",
                "identifier": {
                    "type": "identifier",
                    "blip_type": "string",
                    "name": "data"
                },
                "pattern": [
                    {
                        "type": "string_literal",
                        "blip_type": "string",
                        "value": "["
                    },
                    {
                        "type": "identifier",
                        "blip_type": "string",
                        "name": "num"
                    },
                    {
                        "type": "string_literal",
                        "blip_type": "string",
                        "value": "]"
                    }
                ]
            },
            "body": [
                {
                    "type": "return",
                    "expression": {
                        "type": "concatenation",
                        "blip_type": "string",
                        "operands": [
                            {
                                "type": "string_literal",
                                "blip_type": "string",
                                "value": "found number: "
                            },
                            {
                                "type": "identifier",
                                "blip_type": "string",
                                "name": "num"
                            }
                        ]
                    }
                }
            ],
            "else": [
                {
                    "type": "return",
                    "expression": {
                        "type": "string_literal",
                        "blip_type": "string",
                        "value": "not a bracketed number"
                    }
                }
            ]
        }
    ],
    "directives": {
        "input": {
            "type": "fixed",
            "value": 1
        },
        "output": {
            "type": "fixed",
            "value": 1
        }
    }
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`["[123]"]`|`["found number: 123"]`|
|`["abc"]`|`["not a bracketed number"]`|
|`["[]"]`|`["found number: "]`|

## Capturing Variables Bound In The Outer Scope

A capture assigns to the variable it names, just as `=` does. Where that variable was already bound before the `if`, the
capture writes to it, and the new value outlives the block.

A failed match binds nothing at all, so the variable still holds what it held before the `if` was reached. That is what makes
the pattern below a way of saying "use the captured text if it was there, and keep the default otherwise".

The `if` block is empty because the capture is the whole of its effect.

#### Blip code

```blip
label = "unknown"

line = input[0]

if line -> "name:" label { }

ret label
```

#### Blip IR

<details>
<summary><i>Expand...</i></summary>

```json
{
    "type": "program",
    "statements": [
        {
            "type": "assignment",
            "identifier": {
                "type": "identifier",
                "blip_type": "string",
                "name": "label"
            },
            "expression": {
                "type": "string_literal",
                "blip_type": "string",
                "value": "unknown"
            }
        },
        {
            "type": "assignment",
            "identifier": {
                "type": "identifier",
                "blip_type": "string",
                "name": "line"
            },
            "expression": {
                "type": "index",
                "blip_type": "string",
                "identifier": {
                    "type": "identifier",
                    "blip_type": "list[string]",
                    "name": "input"
                },
                "index": {
                    "type": "integer_literal",
                    "blip_type": "integer",
                    "value": 0
                }
            }
        },
        {
            "type": "if",
            "condition": {
                "type": "decomposition_test",
                "identifier": {
                    "type": "identifier",
                    "blip_type": "string",
                    "name": "line"
                },
                "pattern": [
                    {
                        "type": "string_literal",
                        "blip_type": "string",
                        "value": "name:"
                    },
                    {
                        "type": "identifier",
                        "blip_type": "string",
                        "name": "label"
                    }
                ]
            },
            "body": []
        },
        {
            "type": "return",
            "expression": {
                "type": "identifier",
                "blip_type": "string",
                "name": "label"
            }
        }
    ]
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`["name:bob"]`|`["bob"]`|
|`["name:"]`|`[""]`|
|`["nothing"]`|`["unknown"]`|
