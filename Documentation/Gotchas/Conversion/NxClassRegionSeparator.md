# The NX class region terminator is not always `02`

## Expectation

The modern SPLMSSTR type registry has three regions. The reference region ends with `01`, the class
region ends with `02`, and the member region runs to the end of the registry. A writer can therefore
emit `02` after the last class.

## Actual behaviour

The class region terminator is an opaque separator byte, not a fixed marker. Measured on the corpus:

```text
part             class region terminator
wave_modern.prt  7f
empty.prt        77
flange_modern.prt 02
fresh_block.prt  02
dim40.prt        02
```

A reader that requires `02` stops early on `wave_modern.prt` and `empty.prt`, and a writer that
always emits `02` produces a class table that differs from the source at the terminator.

## Workaround

`ClassTable.ReadClasses` returns the separator byte it stopped on, `Registry` carries it, and
`ClassTable.WriteClasses` emits it. Do not assume `02`.

## Evidence

`WriteRegistry(ReadRegistry(payload))` reproduces the class table byte for byte on all five parts
once the separator is carried. See
[the class table grammar](../../../Changes/Nx/NxClassTableGrammar.md).
