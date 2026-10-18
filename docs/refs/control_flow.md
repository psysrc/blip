# Control Flow

`if` statements check a boolean, and only execute the following block if the expression equates to `true`. An optional `else` block can be provided which will run when the boolean expression equates to `false`.

`while` and `for` loops are described in the [Language Reference](../language_reference.md) but are not implemented yet; see
the [to-do list](../todo.md) for what is still outstanding.

## If With A Boolean Condition

An `if` runs its block only when its condition is true.

The condition has to be a boolean.

#### Blip code

```blip
!in 1

verbose = true

if verbose {
    ret ["verbose", input[0]]
}

ret [input[0]]
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
                "blip_type": "boolean",
                "name": "verbose"
            },
            "expression": {
                "type": "boolean_literal",
                "blip_type": "boolean",
                "value": true
            }
        },
        {
            "type": "if",
            "condition": {
                "type": "identifier",
                "blip_type": "boolean",
                "name": "verbose"
            },
            "body": [
                {
                    "type": "return",
                    "expression": {
                        "type": "list",
                        "blip_type": "list[string]",
                        "elements": [
                            {
                                "type": "string_literal",
                                "blip_type": "string",
                                "value": "verbose"
                            },
                            {
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
                        ]
                    }
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
                ]
            }
        }
    ],
    "directives": {
        "input": {
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
|`["data"]`|`["verbose", "data"]`|

## Conditional Decomposition

A decomposition can be used as a condition. If the string fits the pattern, the condition is true and the block runs with
every capture bound. If it does not fit, the block is skipped and the program carries on.

The captures belong to the block. They are not bound after it, because a failed match never bound them at all - so there is no
value they could sensibly have on the path where the pattern did not fit.

#### Blip code

```blip
!in 1

email = input[0]

if email -> name "@" domain {
    ret name
}

ret "not an email address"
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
                "name": "email"
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
                    "name": "email"
                },
                "pattern": [
                    {
                        "type": "identifier",
                        "blip_type": "string",
                        "name": "name"
                    },
                    {
                        "type": "string_literal",
                        "blip_type": "string",
                        "value": "@"
                    },
                    {
                        "type": "identifier",
                        "blip_type": "string",
                        "name": "domain"
                    }
                ]
            },
            "body": [
                {
                    "type": "return",
                    "expression": {
                        "type": "identifier",
                        "blip_type": "string",
                        "name": "name"
                    }
                }
            ]
        },
        {
            "type": "return",
            "expression": {
                "type": "string_literal",
                "blip_type": "string",
                "value": "not an email address"
            }
        }
    ],
    "directives": {
        "input": {
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
|`["bob@example.com"]`|`["bob"]`|
|`["nonsense"]`|`["not an email address"]`|

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

## A Variable Bound In Every Branch

A variable assigned in *every* branch is still bound after the `if`.

Assign it in only one branch and it is not bound afterwards, because there is a path through the `if` that never set it. An
`if` with no `else` always has such a path, so nothing a lone block binds survives it. Both of those are compile errors where
the name is used - see [Static Errors](static_errors.md).

#### Blip code

```blip
!in 1

flag = true

if flag {
    label = "yes"
} else {
    label = "no"
}

ret label " " input[0]
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
                "blip_type": "boolean",
                "name": "flag"
            },
            "expression": {
                "type": "boolean_literal",
                "blip_type": "boolean",
                "value": true
            }
        },
        {
            "type": "if",
            "condition": {
                "type": "identifier",
                "blip_type": "boolean",
                "name": "flag"
            },
            "body": [
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
                        "value": "yes"
                    }
                }
            ],
            "else": [
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
                        "value": "no"
                    }
                }
            ]
        },
        {
            "type": "return",
            "expression": {
                "type": "concatenation",
                "blip_type": "string",
                "operands": [
                    {
                        "type": "identifier",
                        "blip_type": "string",
                        "name": "label"
                    },
                    {
                        "type": "string_literal",
                        "blip_type": "string",
                        "value": " "
                    },
                    {
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
                ]
            }
        }
    ],
    "directives": {
        "input": {
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
|`["x"]`|`["yes x"]`|

## Nested Conditionals

Blocks can nest, so a decomposition can be tried on something an outer decomposition captured.

`ret` ends the whole program rather than just the block it sits in.

#### Blip code

```blip
!in 1

path = input[0]

if path -> dir "/" rest {
    if rest -> stem ".txt" {
        ret ["dir", dir, "stem", stem]
    }

    ret ["dir", dir]
}

ret ["no directory"]
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
                "name": "path"
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
                    "name": "path"
                },
                "pattern": [
                    {
                        "type": "identifier",
                        "blip_type": "string",
                        "name": "dir"
                    },
                    {
                        "type": "string_literal",
                        "blip_type": "string",
                        "value": "/"
                    },
                    {
                        "type": "identifier",
                        "blip_type": "string",
                        "name": "rest"
                    }
                ]
            },
            "body": [
                {
                    "type": "if",
                    "condition": {
                        "type": "decomposition_test",
                        "identifier": {
                            "type": "identifier",
                            "blip_type": "string",
                            "name": "rest"
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
                                "value": ".txt"
                            }
                        ]
                    },
                    "body": [
                        {
                            "type": "return",
                            "expression": {
                                "type": "list",
                                "blip_type": "list[string]",
                                "elements": [
                                    {
                                        "type": "string_literal",
                                        "blip_type": "string",
                                        "value": "dir"
                                    },
                                    {
                                        "type": "identifier",
                                        "blip_type": "string",
                                        "name": "dir"
                                    },
                                    {
                                        "type": "string_literal",
                                        "blip_type": "string",
                                        "value": "stem"
                                    },
                                    {
                                        "type": "identifier",
                                        "blip_type": "string",
                                        "name": "stem"
                                    }
                                ]
                            }
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
                                "type": "string_literal",
                                "blip_type": "string",
                                "value": "dir"
                            },
                            {
                                "type": "identifier",
                                "blip_type": "string",
                                "name": "dir"
                            }
                        ]
                    }
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
                        "type": "string_literal",
                        "blip_type": "string",
                        "value": "no directory"
                    }
                ]
            }
        }
    ],
    "directives": {
        "input": {
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
|`["docs/notes.txt"]`|`["dir", "docs", "stem", "notes"]`|
|`["docs/notes.md"]`|`["dir", "docs"]`|
|`["notes.txt"]`|`["no directory"]`|
