# The small `5f` records are a zero run with a free flag

## Behaviour

Twelve section-0 records share the frame `02 02 ff 00 5f 01 04 01`. Two of them carry
a zero run ending in a flag byte; the rest are 78 to 4374 bytes of mixed content:

```text
10   02 02 ff 00 5f 01 04 01 00 01
14   02 02 ff 00 5f 01 04 01 00 00 00 00 00 01
```

`ObjectSection.SmallRecord(Length, TailFlag)` builds one and `ReadSmallRecord` reads it,
rejecting any record whose payload is not a zero run so the large mixed shapes are out of
scope rather than mis-parsed.

## Verification

Byte-exact across four fixtures:

```text
dim40.prt        2 reproduced 0 mismatched 248 not small
const_box60.prt  2 reproduced 0 mismatched 248 not small
empty.prt        2 reproduced 0 mismatched 212 not small
var_blank.prt    2 reproduced 0 mismatched 212 not small
```

Mutation, each loaded in NX 2506:

```text
14 byte record trailing 01 -> 02        loads
14 byte record an inner 00 -> 01        loads
10 byte record trailing 01 -> 02        loads
17 byte record first token byte changed loads
```

So the flag and the zero run are free: the value is not a count NX reconciles on load.

## Limits

- The flag's meaning is not known; it is free, not derived, so re-emitting it produces the
  same byte and section 0's provenance does not move.
- The ten large members of the family are still carried and are not covered by this
  grammar.
