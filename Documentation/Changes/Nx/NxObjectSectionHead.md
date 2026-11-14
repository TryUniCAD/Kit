# The writer emits the root object section's head record

## Behaviour

`convert.adapters.nx.ObjectSection.HeadRecord` builds the head record of the root
object section (record 0 of section 0) from a part text: the tag
`41 00 03 03`, a length prefix of `len(text) + 2`, the text, a terminator, the
anchor, the seven byte identity and the fixed tail.

`nx.author_sections` now replaces that record with one naming the path being
written, and `ReplaceHead` rebuilds the section with the record table renumbered
and the section pointer shifted by the size change.

## Field grammar, measured by mutation

Single fields were patched in `empty.prt`'s section 0 and each part was loaded in
NX 2506:

```text
head tag 0x41 -> 0x42                  refuses
head kind 03 03 -> 03 04               refuses
head length prefix 0x22 -> 0x21        refuses
head length prefix 0x22 -> 0x23        refuses
head path text changed, same length    loads
head path text changed, other length   loads, once the pointer is shifted
head anchor e0 6a f8 -> e0 6a f9       loads
head identity replaced by ff x 7       loads
head last two bytes changed            loads
record 4 bytes changed                 loads
record 3 and 6 eight byte id changed   loads
record 3 last ten bytes zeroed         loads
record 1 or 2 tail zeroed              refuses
class identifier in the header changed refuses
```

So the validated fields are the record tags, the length prefixes and the index
lists; the free fields are the path text, the anchor, the identity, the instance
ids and the trailing words. That is what makes the head record emittable.

## Verification

The head record reproduces the source byte for byte when given its text, apart
from the identity, and the whole section then matches exactly:

```text
empty.prt        7 differing bytes (the identity)   33395 == 33395
multi.prt        6 differing bytes                  33395 == 33395
var_blank.prt    7 differing bytes                  33407 == 33407
const_box60.prt  0 differing bytes (head kept)      36694 == 36694
dim40.prt        0 differing bytes (head kept)      36694 == 36694
```

Writing through the adapter and opening in NX 2506:

```text
obj4_empty.prt        bodies 0  exprs 0   head text names the written path
obj4_const_box60.prt  bodies 1  exprs 3
obj4_dim40.prt        bodies 1  exprs 3
```

`TestNxObject` checks the head layout, the empty-text guard, the short-identity
guard, the object count reader and the zero-count guard.

## Limits

- The head tail carries two variable length integers that differ per document
  (`80 d5 02` for `empty.prt`, `fa 02` for a part with a body), so the record is
  emitted only when the generated length matches the source. A part with a body
  keeps its source head.
- The other 213 records, the class table and the identifiers are still carried
  from the source part, so no part is written without a source document yet.
