# Bounding spheres use native addition order

Replacing a fixed native sequence of double additions with Python's floating-point `sum` can change the stored sphere radius by one unit in the last place. Both results can be geometrically accurate while their serialized bytes differ.

The SDK linked-drawing construction proof exposed this on a new 29.3 × 17.9 × 21.1 mm prism. The compensated-sum expression produced radius `0x1.4a23bef8c6791p-6`; the independent constructor produced `0x1.4a23bef8c6790p-6`. Every other logical stream and all other floating fields agreed. The mismatch was confined to the shared local-body radius in the view and its internal reference.

The pinned native box setter computes the three squared differences, adds them in the fixed native sequence, takes the square root and multiplies by one half. Preserve that expression as `sqrt(dx*dx + dy*dy + dz*dz) * 0.5`. Do not replace it with a generic reduction when exact arithmetic ordering is part of the construction comparison. The [2026 box trace](../../../../../../re/solidworks/records/AssemblyConstruction2026.md#computed-geometric-bounds) records the owner and field rule. This is an offline construction precision finding, without new native acceptance.
