# Basic Programs

## Hello World

#### Blip code

```blip
// Comments start with a double-slash
# Comments can also start with a hash

// This Blip program simply returns the hard-coded string "Hello, World!"
// The `ret` keyword is used to return the expression from the program.

ret "Hello, World!"
```

#### Blip IR

<details>
<summary><i>Expand...</i></summary>

```json
{
    "type": "program",
    "statements": [
        {
            "type": "return",
            "expression": {
                "type": "expression",
                "value": {
                    "type": "string_literal",
                    "value": "Hello, World!"
                }
            }
        }
    ]
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`[]`|`["Hello, World!"]`|
|`["input isn't used"]`|`["Hello, World!"]`|

## Hello World (alternative)

#### Blip code

```blip
// This version of Hello World uses single-quotes ' instead of double quotes "

ret 'Hello, World!'
```

#### Blip IR

<details>
<summary><i>Expand...</i></summary>

```json
{
    "type": "program",
    "statements": [
        {
            "type": "return",
            "expression": {
                "type": "expression",
                "value": {
                    "type": "string_literal",
                    "value": "Hello, World!"
                }
            }
        }
    ]
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`[]`|`["Hello, World!"]`|

## Empty Program

Programs in Blip always either return a valid output, or produce an error.
So, the empty program below - which does not return any output - will always produce an error.

#### Blip code

```blip
// Nothing
```

#### Blip IR

<details>
<summary><i>Expand...</i></summary>

```json
{
    "type": "program",
    "statements": []
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`[]`|`Error`|

## Identity Program

The identity program returns the same strings that were provided to it.
This is achieved by returning the special `input` variable, which is a list of all input strings.

#### Blip code

```blip
ret input
```

#### Blip IR

<details>
<summary><i>Expand...</i></summary>

```json
{
    "type": "program",
    "statements": [
        {
            "type": "return",
            "expression": {
                "type": "expression",
                "value": {
                    "type": "identifier",
                    "name": "input"
                }
            }
        }
    ]
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`[]`|`[]`|
|`["hello"]`|`["hello"]`|
|`["a", "b", "c"]`|`["a", "b", "c"]`|

## Variable Assignment

#### Blip code

```blip
my_name = "Sam"
my_username = my_name
ret my_username
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
                "name": "my_name"
            },
            "expression": {
                "type": "expression",
                "value": {
                    "type": "string_literal",
                    "value": "Sam"
                }
            }
        },
        {
            "type": "assignment",
            "identifier": {
                "type": "identifier",
                "name": "my_username"
            },
            "expression": {
                "type": "expression",
                "value": {
                    "type": "identifier",
                    "name": "my_name"
                }
            }
        },
        {
            "type": "return",
            "expression": {
                "type": "expression",
                "value": {
                    "type": "identifier",
                    "name": "my_username"
                }
            }
        }
    ]
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`[]`|`["Sam"]`|

## Concatenation

Strings next to each other are implicitly concatenated.
This applies to string literals as well as string variables.

#### Blip code

```blip
abc = "A" "B" "C"           // abc == "ABC"
my_str = abc "123" abc      // my_str == "ABC123ABC"
ret my_str
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
                "name": "abc"
            },
            "expression": {
                "type": "expression",
                "value": {
                    "type": "concatenation",
                    "operands": [
                        {
                            "type": "string_literal",
                            "value": "A"
                        },
                        {
                            "type": "string_literal",
                            "value": "B"
                        },
                        {
                            "type": "string_literal",
                            "value": "C"
                        }
                    ]
                }
            }
        },
        {
            "type": "assignment",
            "identifier": {
                "type": "identifier",
                "name": "my_str"
            },
            "expression": {
                "type": "expression",
                "value": {
                    "type": "concatenation",
                    "operands": [
                        {
                            "type": "identifier",
                            "name": "abc"
                        },
                        {
                            "type": "string_literal",
                            "value": "123"
                        },
                        {
                            "type": "identifier",
                            "name": "abc"
                        }
                    ]
                }
            }
        },
        {
            "type": "return",
            "expression": {
                "type": "expression",
                "value": {
                    "type": "identifier",
                    "name": "my_str"
                }
            }
        }
    ]
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`[]`|`["ABC123ABC"]`|

## Decomposition

Strings can be decomposed into constituent parts using the decomposition operator `->`.
This simultaneously verifies that the string follows the expected pattern, throwing an error if not.

#### Blip code

```blip
// Assume the input is an email, e.g. harvey.madson@hotmail.co.uk
email = input[0]
email -> username "@" *
username -> first "." last
ret first " " last
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
                "name": "email"
            },
            "expression": {
                "type": "expression",
                "value": {
                    "type": "index",
                    "identifier": {
                        "type": "identifier",
                        "name": "input"
                    },
                    "index": {
                        "type": "integer_literal",
                        "value": 0
                    }
                }
            }
        },
        {
            "type": "decomposition",
            "identifier": {
                "type": "identifier",
                "name": "email"
            },
            "pattern": [
                {
                    "type": "identifier",
                    "name": "username"
                },
                {
                    "type": "string_literal",
                    "value": "@"
                },
                {
                    "type": "decomposition_wildcard"
                }
            ]
        },
        {
            "type": "decomposition",
            "identifier": {
                "type": "identifier",
                "name": "username"
            },
            "pattern": [
                {
                    "type": "identifier",
                    "name":"first"
                },
                {
                    "type": "string_literal",
                    "value": "."
                },
                {
                    "type": "identifier",
                    "name": "last"
                }
            ]
        },
        {
            "type": "return",
            "expression": {
                "type": "expression",
                "value": {
                    "type": "concatenation",
                    "operands": [
                        {
                            "type": "identifier",
                            "name": "first"
                        },
                        {
                            "type": "string_literal",
                            "value": " "
                        },
                        {
                            "type": "identifier",
                            "name": "last"
                        }
                    ]
                }
            }
        }
    ]
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`["harvey.madson@hotmail.co.uk"]`|`["harvey madson"]`|
|`["amy.nelson@gmail.com"]`|`["amy nelson"]`|
|`["Not an email"]`|`Error`|

## Indexing into Lists

Lists store a number of elements (zero or more).
Indexing into a list will provide the element at that position.
Indexes start at 0.

The program below returns the first string provided to the program.

#### Blip code

```blip
ret input[0]
```

#### Blip IR

<details>
<summary><i>Expand...</i></summary>

```json
{
    "type": "program",
    "statements": [
        {
            "type": "return",
            "expression": {
                "type": "expression",
                "value": {
                    "type": "index",
                    "identifier": {
                        "type": "identifier",
                        "name": "input"
                    },
                    "index": {
                        "type": "integer_literal",
                        "value": 0
                    }
                }
            }
        }
    ]
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`[]`|`Error`|
|`["a"]`|`["a"]`|
|`["a", "b"]`|`["a"]`|
|`["a", "b", "c"]`|`["a"]`|
