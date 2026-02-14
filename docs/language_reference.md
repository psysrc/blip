# Blip Program Syntax

## String Literals

A literal string defined in the program.

Example:

```plaintext
"A literal string"
```

## Variables and Assignment

An arbitrary number of variables can be used in a Blip program to help organise data, just like any other programming
language.

Example:

```plaintext
name = "John"
```

Here is an alternative assignment syntax. It is semantically equivalent to the above but uses different syntax.
This exists because it looks like the logical opposite to a decomposition statement, so gives a nice symmetry:

```plaintext
"John" -> name
```

## String Concatenation

Blip automatically concatenates any strings that appear side by side, similar to Python.

```plaintext
text = "foo" "bar" "baz"  // Result: "foobarbaz"
```

However, this doesn't just apply to string literals. Concatenation also works with variables!

```plaintext
myname = "John"
text = "<<" myname ">>"  // Result: "<<John>>"
```

This is the standard way to combine multiple strings in Blip.

## String Decomposition

String decomposition is the opposite of string concatenation. It's a core language feature that allows you to decompose
a string into component parts whilst also asserting that the string follows an expected pattern.

Decomposition is achieved using the `->` operator.

```plaintext
// This example extracts the first part of an email (everything before the '@' character).

// Blip will decompose the string into the right-hand side expression.
// The literal "@" must match exactly.
// The wildcard "*" matches anything.
// The variable "name" also matches anything, and also captures the text in the variable to be used later.

email = "bob.john@gmail.com"
email -> name "@" *  // name == "bob.john"
```

```
// This example extracts the content from an XML node.

xml = "<foo>Bar</foo>"
xml -> "<foo>" content "</foo>"  // content == "Bar"
```

If decomposition fails because the string doesn't fit the pattern, an error is automatically raised.
As a result, decomposition can be used as a convenient pattern matching syntax.


```
// This example validates that the string is surrounded by square brackets, without extracting any text into a variable:

data = "[good]"
data = "bad"

data -> "[" * "]"  // Throws an error if 'data' doesn't fit the pattern
```

Alternative decompositions can be provided. If a decomposition fails, subsequent alternatives will be tried.

```plaintext
// This example extracts a name from the string.
// The string can be in one of two formats, either "user: <name>" or "email: <name>@<rest of email>".
// This decomposition supports both.

user_data -> "user: " name | "email: " name "@" *
```

## Input and Output Directives

By default, Blip programs are permissive and allow any number of input strings and any number of output strings.
You can use input and output directives to be more restrictive depending on what your program does.

Input directives use the `!in` keyword. This declares how many inputs the program supports.
Output directives use the `!out` keyword. This declares how many outputs the program will provide.

```plaintext
!in 1   // Exactly one string as input
!out 2  // Exactly two strings as output
```

It is recommended to always provide explicit input and output directives for your program.
By doing so it helps catch problems earlier than would otherwise be possible. This is especially true if you are using Blip
programs in a larger software ecosystem (this applies to both interpreted Blip programs as well as transpiled programs).

For example, if your program expects three strings as input, but at runtime is only invoked with two,
it might take your program a long time before it tries to access the third string before it throws a strange error.
In this situation if you had provided an input directive, the problem would have been caught before the program even started running.

Only one input directive can be provided per program, and likewise with the output directive.
Input and output directives are independent from one another; you can provide an input directive without an output directive and vice versa.

Input/output directives support value ranges if your program supports a variable number of inputs/outputs.

```plaintext
!in 1..3    // Accepts 1, 2, or 3 inputs
!in 1..     // Accepts 1 or more inputs
!out ..2    // Provides up to 2 outputs
!out ..     // Provides any number of outputs (same as having no output directive)
```

The input directive has some additional flexibility if the number of input strings is fixed.
Input strings are always accessible using the built-in variable `input`.
However, with a fixed number of inputs you can also directly populate variables from the input strings using the following syntax:

```plaintext
!in username email  // Exactly 2 strings as input: First string becomes 'username', second string becomes 'email'
```

## If Statements

`if` statements create conditional control flow.

```
name = "Sam"

if name == "Sam" {
    ret "Superuser"
}
```

### Conditional Decomposition

Blip also supports `if` statements with conditional decomposition. If the decomposition succeeds, the condition is considered true and the `if` block executes. If it fails, the `if` block is skipped and control moves to the next statement.

```plaintext
email = "bob@example.com"

// Try to decompose the email to check if it contains '@'
if email -> name "@" domain {
    ret name
}
```

This also works with `else` blocks, which execute if the decomposition fails:

```plaintext
data = "[123]"

if data -> "[" num "]" {
    ret "Found number: " num
} else {
    ret "Not a valid number"
}
```

## While Loops

Blip supports `while` loops for repeated iteration with a boolean condition.

```plaintext
counter = 0

while counter < 5 {
    counter = counter + 1
}

ret counter
```

The `while` loop continues as long as the condition is true. The `break` statement can be used to exit the loop early:

```plaintext
counter = 0

while true {
    counter = counter + 1
    if counter >= 10 {
        break
    }
}

ret counter
```

## For Loops

Blip supports `for` loops to iterate over lists and arbitrary ranges.

When iterating over lists, the loop variable is automatically assigned each element from the list.

```plaintext
items = ["a", "b", "c"]

for item in items {
    // Process each item
    // item = "a" then "b" then "c"
}
```

When iterating over ranges, the loop variable starts at 0 and increments by 1 each iteration.

```
for num in 3 {
    // Do something 3 times
    // num = 0 then 1 then 2
}
```

For loops also support the `break` statement to exit the loop early.
