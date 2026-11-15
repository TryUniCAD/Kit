# The NX head identity is six or seven bytes, not always seven

## Expectation

The root object section's head record was read as a fixed layout: tag, length
prefix, text, terminator, prefix, anchor, a seven byte identity and a fixed
nineteen byte suffix. `HeadRecord` required exactly seven identity bytes.

## Actual behaviour

The identity is seven bytes in `empty.prt`, `multi.prt` and `sweep.prt`, but six
bytes in `const_box60.prt` and `dim40.prt`. The suffix is nineteen bytes in every
case. Reading a fixed seven bytes therefore swallows the first suffix byte
(`0x80`) in the six byte parts, and the emitted record no longer matches the
source.

The suffix itself is not a constant. It names the next object id twice and the id
after it once:

```text
empty.prt       80 d5 02 13 04 05 01 00 01 01 80 d5 02 13 80 d6 02 00 00
const_box60.prt 80 fa 02 13 04 05 01 00 01 01 80 fa 02 13 80 fb 02 00 00
```

`0xd5 + 1 = 214` and `0xfa + 1 = 251`, which are the object counts of the two
parts.

## Workaround

`HeadParts` splits the source record at the first `80 <n> 02 13 04 05 01 00`
group after the anchor, so the identity is whatever precedes it. `HeadRecord`
accepts six or seven identity bytes, and `HeadSuffix(NextId)` rebuilds the suffix
from the next object id. `ReplaceHead` uses both, so the head is re-emitted for
both shapes instead of being carried.

## Evidence

`HeadRecord` reproduces the source head byte for byte for `empty.prt`,
`const_box60.prt`, `dim40.prt`, `multi.prt` and `sweep.prt`; `HeadSuffix(214)`
equals the `empty.prt` suffix and `HeadSuffix(251)` equals the `const_box60.prt`
suffix. `TestNxObject` covers both identity lengths and both suffix values.
