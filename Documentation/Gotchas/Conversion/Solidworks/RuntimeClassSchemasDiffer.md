# Archive class schemas are not universally one

## Expectation

Every freshly constructed archive class can use the object helper's schema-one
default because many native controls use that value.

## Actual behavior

The native 2026 loader rejected a generated `uoJournal_c` with file schema one:
the registered runtime class requires schema zero and is not versionable.
The loader reached its `badSchema` path before loading the model graph.
The parent-owned `candidate-H3-schema.json` trace records this negative result.

The shipped `slduiu.dll` independently proves zero at
`uoJournal_c::classuoJournal_c`, preferred address `0x4aef6660`, offset `0x0c`.
The [construction record](../../../../re/solidworks/records/ModelConstruction2026.md)
records the binary and trace hashes.

The follow-up static audit found the same default error in `su_CStringArray`.
Its `swccu.dll` getter `0x31a3de90` returns descriptor `0x31a680c8`, whose
schema at `+0x0c` is zero. Header user/company arrays therefore also require
schema zero. `suObList` instead has schema one, so container classes must not
share an assumed schema.

## Workaround

Construct journals and string arrays with `schema=0`. Determine each class schema from its registered
native class metadata, including the versionable bit, rather than extrapolating
from a document survey or codec round trips. A codec can round-trip a constructed
class header that the target loader rejects.

The same static audit found `moCompRef_c` registered with schema `0xffff` and
no create-object function at `sldmodu` `0x4cf68440`. It is a nonserializable base,
so the standalone factory fails closed; concrete references still use its embedded
field initializer.

The corrected constant comes from the binary and live loader metadata, not a
saved-file field. The complete candidate still requires native acceptance.
