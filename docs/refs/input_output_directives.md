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
    "directives": {
        "input": {
            "type": "fixed",
            "value": 2
        }
    },
    "statements": [
        {
            "type": "return",
            "expression": {
                "type": "expression",
                "value": {
                    "type": "string_literal",
                    "value": "OK"
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
    "directives": {
        "output": {
            "type": "fixed",
            "value": 1
        }
    },
    "statements": [
        {
            "type": "return",
            "expression": {
                "type": "expression",
                "value": {
                    "type": "string_literal",
                    "value": "OK"
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
    "directives": {
        "output": {
            "type": "fixed",
            "value": 2
        }
    },
    "statements": [
        {
            "type": "return",
            "expression": {
                "type": "expression",
                "value": {
                    "type": "string_literal",
                    "value": "OK"
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
    "directives": {
        "input": {
            "type": "fixed",
            "value": 2,
            "names": ["username", "email"]
        }
    },
    "statements": [
        {
            "type": "return",
            "expression": {
                "type": "expression",
                "value": {
                    "type": "identifier",
                    "name": "username"
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
    "directives": {
        "input": {
            "type": "range",
            "min": 1,
            "max": 3
        }
    },
    "statements": [
        {
            "type": "return",
            "expression": {
                "type": "expression",
                "value": {
                    "type": "string_literal",
                    "value": "OK"
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
|`["a"]`|`["OK"]`|
|`["a","b","c"]`|`["OK"]`|
|`["a","b","c","d"]`|`Error`|

## Range Output Directive

#### Blip code

```blip
!out ..2
ret "OK"
```

#### Blip IR

<details>
<summary><i>Expand...</i></summary>

```json
{
    "type": "program",
    "directives": {
        "output": {
            "type": "range",
            "min": null,
            "max": 2
        }
    },
    "statements": [
        {
            "type": "return",
            "expression": {
                "type": "expression",
                "value": {
                    "type": "string_literal",
                    "value": "OK"
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
|`[]`|`["OK"]`|
