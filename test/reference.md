# Reference Programs

This document contains example Blip programs, along with their Blip Intermediate Representation (Blip IR), and example runs with string inputs and outputs.

These references are automatically executed by the Blip test suite so they're always up to date!

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
