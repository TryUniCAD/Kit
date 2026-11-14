# NX part name appears in five streams

## Expectation

Renaming a part should only need the section headers and the saved file name to
change, because the container directory stores stream names, not the part name.

## Observed behavior

NX 2506 stores the part file name in five places:

```text
/Root/FastLoad/RMFastLoad
/Root/FastLoad/Structure
/Root/FastLoad/ExternalReferences
/Root/UG_PART/UG_PART
/Root/UG_PART/ExternalReferences
```

A rewrite that changes only `UG_PART` loads, but the reader then reports both
the old and the new reference, and `RMFastLoad` still names the old file.

## Workaround

Replace the name in every stream that contains it, then rebuild the directory
and recompute both seals. The name is addressed by absolute offsets in the
object-model middle, so the replacement must keep the same byte length. A
different length has to move every offset in that lane, which the adapter
refuses.

## Evidence

`block.prt` rewritten as `black.prt` through the adapter loaded in NX 2506 with
one body, `DATUM_CSYS` and `BLOCK`, six expressions, volume
`23999.999999999996`, area `5200`, and mass `0.18793536`. The written file
contained no occurrence of the old name, and the reader reported only
`black.prt`.
