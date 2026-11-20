# Resolve a through cut's effective direction

## Expectation

The saved reversal bit supplies the signed cut direction by itself on any supported sketch plane.

## Actual behavior

The disclosed two-stock circular cut has a positive Front normal and native reversal word one. The effective tool direction is positive Z. The ordinary blind stock on that datum also extends in positive Z with its reversal word zero. The saved SDK view currently preserves the native through termination and flag without filling the effective direction vector.

## Workaround

Bind the actual selected stock, signed support and through direction during source translation. Supply an explicit effective world vector to the neutral geometry constructor. Require that the signed ray covers the selected blind extent. [Native scope and geometry](../../../../../../re/solidworks/records/ThroughAllMultiStockArchive2026.md) · [Neutral projection and signed controls](../../../../../../re/solidworks/records/TwoStockColdGeometry2026.md)
