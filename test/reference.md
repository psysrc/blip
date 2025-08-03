# Reference Programs

This document contains example Blip programs, along with their Blip Intermediate Representation (Blip IR), and example program executions with string inputs and outputs.

This document is also the core Blip test suite! The information on this page is parsed automatically and executed in the unit tests, meaning it remains up to date as the code changes.

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

## Empty Program

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
