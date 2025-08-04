# Basic Programs

## Hello World

#### Blip code

```blip
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

## Hello World (alternative with comments)

#### Blip code

```blip
# This version of Hello World uses single-quotes ' instead of double quotes "
// Comments can be made with either a hash (#) or double slashes (//)

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

Empty programs are not valid because they halt without producing any output.
Programs in Blip must either explicitly return valid output, or produce an error.

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
