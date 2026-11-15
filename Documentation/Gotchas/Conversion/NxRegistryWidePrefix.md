# NX registry wide tokens use the `a0` prefix, not `90`

## Expectation

The registry token grammar has three wide prefixes: `90`, `a0..af`, and `f1`. The low nibble of the
prefix carries the high 16 bits of the value, so `90` and `a0` both encode a value below `0x10000`.
A writer can pick either.

## Actual behaviour

The vendor never emits `90` in the modern type registry. Every wide token in the corpus uses `a0`
plus the high bits in the low nibble:

```text
value   bytes
5001    a0 13 88
71001   a1 15 58
```

A writer that emits `90` for `5001` produces `90 13 88`, which decodes to the same value but differs
from the source byte. The round trip is then not byte identical.

## Workaround

`ClassTable.WriteToken` emits `0xA0 | ((Value - 1) >> 16)` followed by the low 16 bits. Do not emit
`90`.

## Evidence

`WriteRegistry(ReadRegistry(payload))` reproduces the class table byte for byte on `wave_modern.prt`,
`flange_modern.prt`, `fresh_block.prt`, `empty.prt` and `dim40.prt`. See
[the class table grammar](../../../Changes/Nx/NxClassTableGrammar.md).
