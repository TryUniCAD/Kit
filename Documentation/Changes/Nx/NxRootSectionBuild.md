# The root object model section is generated from parameters

## Behaviour

`re/nx/tools/RootBuild.py` emits the section 3 middle (`UGS::OCC*`,
`UGS::OM::SaveAuditTrail`) from a document counter and the seven byte anchor
identity, instead of carrying it from a saved part. The body is assembled from
named pieces: the flag bytes, the counter, three derived counter values, the
version text, the `SYSTEM` record, the anchor block and the fixed lanes.

The section pointer is derived from the emitted body length, so the generator
does not need the source header.

## Verification

One formula reproduces the section byte for byte in every fixture, including a
different counter:

```text
dim40.prt      counter 0x1e3  176 bytes  identical True
const_box60    counter 0x1e3  176 bytes  identical True
empty.prt      counter 0x1e3  176 bytes  identical True
empty_expr     counter 0x1e8  176 bytes  identical True
multi.prt      counter 0x1e3  176 bytes  identical True
sweep.prt      counter 0x1e3  176 bytes  identical True
```

Splicing that generated body with authored geometry and a stubbed section 4 gives
a part NX 2506 opens and measures:

```text
STATUS 0
BODIES 1
FEATURES 1   BLOCK
EXPRESSIONS 3
VOLUME 36000.0
AREA 7199.999999999999
MASS 0.28190304
```

## Limits

- Sections 1 and 0 are model dependent: 356 bytes with 17 classes for a part
  without a body, 1247 bytes with 30 classes for one with a body, and 27032
  against 28986 bytes with 129 against 154 classes. They encode the construction
  and topology object graph and still come from a saved part.
- The counter is read from the file being rewritten; deriving it from the objects
  a writer emits is part of the remaining payload work.
- Sections 0, 1 and 2 carry model dependent object graphs. Emptying a middle and
  keeping its class and reference lanes makes NX refuse the part, and the same
  section differs by one byte between a 40 and a 60 length box, so those sections
  must be emitted as objects rather than as constants.
