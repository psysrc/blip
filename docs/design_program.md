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

## 0 input strings?

A blip program that does not use any of its input strings will always produce the same result.

In this, a 0-input Blip program is a fancy way of returning a hard-coded list of strings.

## 0 output strings?

A blip program that does not output any strings is still useful, because Blip programs can fail.

If the input strings do not conform to an expected format, or some preconditions do not hold, Blip can produce
an error result.

In this, a 0-output Blip program is a useful way to validate input strings.
