# Decimal placement archive replay

The published decimal placement campaign contributes 69 distinct SOLIDWORKS
parts from 23 complete source-authoring brackets. The exact manifest at
`881d05f3e3fc432f939081acd321ae3eed50eb01` binds each native source by SHA-256.
The sources use all three principal planes and both extrusion directions.
One failed bracket and the separate desktop canaries remain outside this
replay cohort. [Source campaign](https://github.com/TryUniCAD/Kit/blob/881d05f3e3fc432f939081acd321ae3eed50eb01/re/NativePlacement2026/README.md)

Every file uses container version 4 and archive model version 19000. At
codec revision `660100bffe19eb22795c34006516feb369286674`, fifteen selected
document streams and both Parasolid partition streams re-emit byte for byte.
There are 1,173 exact binary comparisons and 69 exact KeyWords comparisons.
KeyWords are read as XML and reframed with the matching ordinary spacing
rule. Both independent processes produced the same receipt, including each
source hash, each binary stream report digest and the linked partition owners.
[Archive receipt](../measurements/2026/DecimalPlacementArchiveReplay01.json)

The active partition and its rollback reconstruct both Parasolid payloads
from typed resident records and history marks. The frame serializer computes
each compressed extent. The SDK's selected and preceding marks agree with
the feature and activation records in the linked archive. The separate
ghost partition reconstructs the origin point and binds the actual body
attribute to the configuration's type-20 manager entry. The observed
`fa0` value is `-1`. Its wider meaning remains unqualified.
[Partition measurement](../../tooling/sw2026/MeasurePrismPartitions.py)

The published source records attest the 19000 archive marker. The replay
does not attest the exact patch build of the origin application's executable.
It starts no native process and publishes no target file. Native edit,
whole-document conversion and FreeCAD benchmark counts receive zero credit.

Run the [audit](../../tooling/sw2026/AuditDecimalPlacementArchive.py) from
the repository root with the pinned codec present and a new output path.

```sh
python3.14 -E -B re/tooling/sw2026/AuditDecimalPlacementArchive.py \
  660100bffe19eb22795c34006516feb369286674 /tmp/DecimalPlacementArchiveReplay.json
```
