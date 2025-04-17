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

## String Decomposition

Decomposition is a core language feature that allows you to extract substrings and assert that a string follows an
expected pattern. Decomposition uses the `->` operator.

```plaintext
// This example extracts the first part of an email (everything before the '@' character).
// It also uses the wildcard character '*' to ignore everything after the '@'.

email = "bob.john@gmail.com"
email -> name "@" *  // The 'name' variable now contains "bob.john"
```

```
// This example extracts the content from an XML node.

xml = "<foo>Bar</foo>"
xml -> "<foo>" content "</foo>"  // The 'content' variable now contains "Bar"
```


If decomposition fails because the provided string doesn't fit the pattern, an error is automatically raised.
As a result, decomposition can be used as a convenient pattern matching syntax.

```
// This example simply validates that the string is surrounded by square brackets, without extracting any text:

data = "[good]"
data = "bad"

data -> "[" * "]"  // No-op if decomposition succeeds; causes an error on failure
```

Alternative decompositions can be provided. If a decomposition fails, subsequent alternatives will be tried.

```plaintext
// This example extracts a name from the string.
// The string can be in one of two formats, either "user: <name>" or "email: <name>@<rest of email>".
// This decomposition supports both.

user_data -> "user: " name | "email: " name "@" *
```

## Input and Output

Blip programs can support zero or more input strings, and zero or more output strings.

By default, all Blip programs are permissive and allow any number of inputs and outputs.
This means even if your program only ever uses the first input string, there's nothing stopping the caller
from providing you with a bunch more. There is also nothing stopping the caller from providing you with no strings
at all! (Though this would almost certainly result in an error.)
This also means by default, any return statements in a Blip program are free to return whatever they want.
They can return an empty list, a single string, or a thousand strings.

For simple Blip programs, this permissiveness is probably okay. However, for more complicated programs, it is
recommended to use input/output declarations.

An input declaration uses the `!in` keyword. This declares how many inputs the program supports.
An output declaration uses the `!out` keyword. This declares how many outputs the program may provide.

```plaintext
!in 1   // Exactly one string as input
!out 2  // Exactly two strings as output
```

These declarations are independent - you can provide an input declaration without an output declaration and vice versa.

Input/output declarations also support value ranges.

```plaintext
!in 1..3   // Accepts 1, 2, or 3
!in 1..    // Accepts 1 or more

!out ..2   // Outputs up to 2
```

With the input declaration `!in`, you have some optional flexibility.
By default, input strings are provided via the built-in variable `input`. This is a list containing all input strings.
However, if you know exactly how many strings your program takes, you can provide named variables to the input
declaration to automatically populate them.

```plaintext
!in username email  // Exactly 2 strings as input: First string becomes 'username', second string becomes 'email'
```
