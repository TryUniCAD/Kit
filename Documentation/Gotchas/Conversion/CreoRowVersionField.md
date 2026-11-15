# A Creo directory row carries its own table version

## Expectation

Directory rows are fixed width and their fields are the same in every container, so a rebuild tool can write
them from a constant template — name, offset, length, expanded size, version, kind, count and two checksums.

## Actual behaviour

The fifth field is a **version**, and it differs between files. The retained control writes `1934`; the ladder
control writes `2963`. `re/creo/tools/Subset.py` hardcoded `1934`, so rebuilding the ladder rewrote 174 bytes of
its directory and the result was no longer byte-identical:

```text
empty/solid_start_part_mmks.prt  81539 ->  81539  byte-identical: True
ladder1.prt.2                   110065 -> 110065  byte-identical: False   (first diff at 900)
```

Original row field: `... 4fe 681 2963 a 1 0b8c 3ffd`
Rebuilt row field:  `... 4fe 681 1934 a 1 0b8c 3ffd`

The no-op rebuild was byte-identical only for the file whose version happened to match the constant, which made
the tool look correct while it silently corrupted any other container.

## Workaround

Carry the version through from the row being rewritten instead of writing a constant. `Subset.Row` now stores it
and `RowValue` writes it back, after which both retained files round-trip byte-identically:

```text
empty/solid_start_part_mmks.prt    byte-identical no-op: True
ladder1.prt.2                      byte-identical no-op: True
```

An earlier version of this note said that replacing a section with a shorter body produced an extent our own
reader rejects (`Creo table row 'FeatDefs' has an invalid extent`). That was wrong: it came from passing a bare
payload where the builder expects the whole `#<name>\n` body. With the body wrapped correctly the replacement
works and the file reads back.

## Evidence

- `re/creo/tools/Subset.py` — `Row.version`, `ReadTable`, `RowValue`.
- `Documentation/Gotchas/Conversion/CreoCompressedRowMagic.md` — the other row-field trap found the same way.
