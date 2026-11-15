# The class registry is a static table of name pairs in libpart.dll

## Behaviour

No writer behaviour changed. This records the structure that was recovered from the vendor module,
which is where a class-table emitter would have to get its values from.

## What was measured

A pure-Python PE stack (`pefile` + `capstone`) reads the module on the host, which the broken Hopper
provider cannot. The registry string sits at

```text
file offset 0xb75398    VA 0x180b76998    .text base 0x180001000, size 0xae1600
```

and two `lea` instructions reference it, at `0x180144783` and `0x180366d1f`. Both build the same
structure on the stack, and disassembling them resolves every operand:

```text
0x180144744 -> 0x180368d80   (binary)
0x180144753 -> 0x180277500   '@SH'
0x180144763 -> 0x1812065b8   (binary)
0x180144777 -> 0x180b714c0   'UGS::PART'
0x180144783 -> 0x180b76998   'UGS::OM::RootObjectGroup'
0x18014478f -> 0x18120d3a0   (binary)
             immediate 2, immediate 4, immediate 0x21000
```

so a registry entry is a static descriptor holding a **parent name** (`UGS::PART`) and a **class
name** (`UGS::OM::RootObjectGroup`), plus flags. The second xref builds the same descriptor, so this
is one entry emitted twice rather than two different cases.

## Why this matters

The 71-80 bit value is computed at load, not stored, and the descriptor carries a parent name. That
makes a chain the natural model: a class's value derived from its parent's value plus its own name,
with `UGS::PART` at the root. That is a different shape from everything tested so far — 22 name-only
functions — and it is testable against the corpus, since the file's table is ordered with the root
classes first.

## Limits

- The routine that consumes the descriptor has not been read; only the descriptor construction.
- The file's names are the short form (`UGS::OM::RootObject`) while the registry uses
  (`UGS::OM::RootObjectGroup`), which is not yet reconciled.
- `Writer.py` still requires a retained native document.
