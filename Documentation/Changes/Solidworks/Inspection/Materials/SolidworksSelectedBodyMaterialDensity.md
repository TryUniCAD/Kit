# Observe assigned material through the selected solid

The SOLIDWORKS source research runner now measures physical volume, mass and density in SI through `IMassProperty2` on the actual sole solid. It retains the legacy part mass, shape and manual override checks as separate diagnostics.

The disclosed corner probe measured 1000 kg/m³ unassigned and 2700 kg/m³ after assignment, save and fresh read-only reopen across four healthy SOLIDWORKS 2026 SP05.2 processes. The legacy getter reported 1 kg/m³ throughout. [Diagnostic receipt](../../../../../re/solidworks/measurements/2026/AssignedMaterialDensityProbe01.json)

Packet 03 preserves both disclosed designs, their appearance contrasts, the two catalog predictions, and the native material swap and dimension-edit checks. The host freezer verifies the exact prior packet and committed tools before preparing the root-owned native run. Full source lifecycle, held-out qualification and writer support remain pending. [Source protocol](../../../../../re/solidworks/records/AssignedMaterialSourceProtocol2026.md#packet-03-selected-body-measurement)
