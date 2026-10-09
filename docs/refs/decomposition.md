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

## Decomposition Backtracks

A capture runs up to the *first* following occurrence of the literal after it. If after that the pattern doesn't match, the decomposition
can backtrack and try the *next* occurrence of the literal and check the pattern again.

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
