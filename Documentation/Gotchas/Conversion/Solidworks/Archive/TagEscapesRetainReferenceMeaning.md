# Escaped tags retain reference meaning

## Expectation

A word equal to a structural marker has the same meaning wherever it appears in a tag, and class and object index zero both represent null.

## Actual behavior

The pinned 2026 `su_CArchive::ReadClass` first reads u16. Only an original u16 `0xffff` starts a new-class descriptor. An original u16 `0x7fff` instead selects one u32 reference payload. That payload's high bit selects class versus object, and its remaining 31 bits hold the index.

Consequently, escaped u32 `0x0000ffff` is object reference `65535`; escaped u32 `0x80007fff` is class reference `32767`; escaped u32 `0xffffffff` is class reference `0x7fffffff`. None starts a new descriptor. These are consequences of native branches, not captured document rows.

Native load-map initialization reserves object slot zero as null. Both ordinary zero and escaped object zero resolve to that slot. Class index zero is rejected in both short and escaped forms. The [native grammar record](../../../../../re/solidworks/records/ArchiveTagGrammar2026.md) identifies the exact branches, complete extents, and hashes.

The reader accepts overlong references; native writers choose canonical widths. Retaining only kind and index does not preserve an overlong encoding. The previous research `Core.read_class` labeled escaped zero as an object reference, unlike its ordinary null branch; shared tag integration must account for this specific normalization.

## Workaround

Interpret the structural markers at the initial u16 boundary. Decode escaped payloads with unsigned arithmetic and reject class index zero. Keep descriptor parsing and map validation in their owners. Use [the shared tag primitives](../../../../Changes/Solidworks/Model/SolidworksArchiveTagPrimitives.md) for canonical generation, and report the noncanonical replay limit rather than inferring wire width from an integer.
