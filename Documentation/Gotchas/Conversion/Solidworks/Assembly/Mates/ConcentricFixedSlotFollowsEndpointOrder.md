# Concentric fixed ownership follows endpoint order

The portable assembly stores the fixed occurrence in occurrence order.
`MakeCylAsm` then selects the two references in the mate's endpoint order.
The fixed slot passed to `CylMateIn` indexes that ordered pair. Reusing the
original occurrence slot would set `moReference_c.f408` on the other
occurrence when the selections are reversed.

Preserve the original occurrence order and calculate the selected slot with
`EndIndexes.index(Model.FixedIndex)`. Check the actual occurrence backlink
from each active wrapper and the fixed bit on its original reference. The
guarded aligned and anti-aligned cases exercise both selected fixed slots.
[Planning proof](../../../../../../re/solidworks/records/SdkConcentricMatePlanning2026.md)
