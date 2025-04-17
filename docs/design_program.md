# Blip Program Design

Blip programs take a list of strings as input and return a list of strings as output.
The input list can contain 0 or more strings.
Similarly, the output list can contain 0 or more strings.

```mermaid
flowchart LR
    P[Blip Program]
    in[0..N strings]
    out[0..M strings]

    in --> P --> out
```

## Environmental influence and side-effects

Blip programs do not have side-effects.
They cannot print output to the console, make system calls, do networking, interact with peripheral devices, etc.

Similarly, Blip programs cannot be influenced by the environment it executes in.
They cannot read environment variables, read from files, etc.

This means Blip programs are fully isolated from the rest of the world.
The only way to influence a Blip program is via its list of input strings.
The only way a Blip program can influence the world is via its list of output strings.

This makes Blip conceptually simple, and importantly predictable.

## Fail-fast

Blip programs have implicit fail-fast semantics. If a program attempts an operation and it fails, the
program immediately halts and returns an error. This is to help enforce program invariants, and is useful for quickly
validating that strings match particular patterns, or meet certain criteria.

Programs that terminate with an error do not provide normal string output.
They will instead return a single string containing an error message describing the failure.

Stand-alone interpreters will handle these error cases by exiting with a non-zero error code, and printing the
error string to the standard error stream.

Transpiled Blip code will handle this in a manner that is appropriate for the target language.
Exceptions will typically be used for languages that support them.
For languages that do not support exceptions (like C), a special return code will be used instead to distinguish
it from successful output.

## 0 input strings?

A Blip program that does not use any of its input strings will always produce the same result.

In this, a 0-input Blip program is a fancy way of returning a hard-coded list of strings.

## 0 output strings?

A Blip program that does not output any strings is still useful, because Blip programs can fail.

If the input strings do not conform to an expected format, or some preconditions do not hold, Blip can produce
an error result.

In this, a 0-output Blip program is a useful way to validate input strings.
