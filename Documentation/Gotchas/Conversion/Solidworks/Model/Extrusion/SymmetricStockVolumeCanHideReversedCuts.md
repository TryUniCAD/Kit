# Symmetric stock volume can hide reversed cuts

## Expectation

Matching body count, volume and area on a mid-plane stock proves a one-direction through-all cut opens on the right cap.

## Actual behavior

Removing the positive or negative half gives the same volume and area. The through-all cut's default direction in the measured profile follows the negative sketch normal. Its native reverse flag turns it toward the positive normal. Exchanging the two cut directions flips the axial centre of mass and moves the cavity opening.

## Workaround

Bind the actual sketch frame and independent reverse flag. Compare the reconstructed signed rim positions and centre of mass with the oracle or an independent geometric prediction.

See [the cold cut geometry evidence](../../../../../../re/solidworks/records/ThroughAllColdGeometryRead2026.md).
