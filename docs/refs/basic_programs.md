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
