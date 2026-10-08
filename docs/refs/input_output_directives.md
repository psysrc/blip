# Input and Output Directives

## Fixed Input Directive

#### Blip code

```blip
!in 2
ret "OK"
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
                "type": "string_literal",
                "blip_type": "string",
                "value": "OK"
            }
        }
    ],
    "directives": {
        "input": {
            "type": "fixed",
            "value": 2
        }
    }
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`[]`|`Error`|
|`["1"]`|`Error`|
|`["1", "2"]`|`["OK"]`|
|`["1", "2", "3"]`|`Error`|

## Fixed Output Directive (Success case)

#### Blip code

```blip
!out 1
ret "OK"
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
                "type": "string_literal",
                "blip_type": "string",
                "value": "OK"
            }
        }
    ],
    "directives": {
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
|`[]`|`["OK"]`|

## Fixed Output Directive (Error case)

#### Blip code

```blip
!out 2
ret "OK"
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
                "type": "string_literal",
                "blip_type": "string",
                "value": "OK"
            }
        }
    ],
    "directives": {
        "output": {
            "type": "fixed",
            "value": 2
        }
    }
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`[]`|`Error`|

## Named Input Directive

#### Blip code

```blip
!in username email
ret username
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
                "type": "identifier",
                "blip_type": "string",
                "name": "username"
            }
        }
    ],
    "directives": {
        "input": {
            "type": "fixed",
            "value": 2,
            "names": [
                "username",
                "email"
            ]
        }
    }
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`[]`|`Error`|
|`["only"]`|`Error`|
|`["bob","b@e.com"]`|`["bob"]`|

## Range Input Directive

#### Blip code

```blip
!in 1..3
ret "OK"
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
                "type": "string_literal",
                "blip_type": "string",
                "value": "OK"
            }
        }
    ],
    "directives": {
        "input": {
            "type": "range",
            "min": 1,
            "max": 3
        }
    }
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`[]`|`Error`|
|`["a"]`|`["OK"]`|
|`["a","b","c"]`|`["OK"]`|
|`["a","b","c","d"]`|`Error`|

## Range Output Directive (Success case)

#### Blip code

```blip
!out ..1
ret "OK"
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
                "type": "string_literal",
                "blip_type": "string",
                "value": "OK"
            }
        }
    ],
    "directives": {
        "output": {
            "type": "range",
            "min": null,
            "max": 1
        }
    }
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`[]`|`["OK"]`|

## Range Output Directive (Error case)

#### Blip code

```blip
!out ..1
ret ["one", "two"]
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
                "type": "list",
                "blip_type": "list[string]",
                "elements": [
                    {
                        "type": "string_literal",
                        "blip_type": "string",
                        "value": "one"
                    },
                    {
                        "type": "string_literal",
                        "blip_type": "string",
                        "value": "two"
                    }
                ]
            }
        }
    ],
    "directives": {
        "output": {
            "type": "range",
            "min": null,
            "max": 1
        }
    }
}
```

</details>

#### Execution

|Input|Output|
|-----|------|
|`[]`|`Error`|
