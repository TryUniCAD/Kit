# One native centre can have two portable binary64 values

A SOLIDWORKS 2026 save can store identical metre bits in the actual
circle centre slot and a fixed-point marker. The circle reader
multiplies those values by 1,000. The legacy marker path rounds
that product to 12 decimal places. In the measured mid-plane saves,
the two portable X values differ by one unit in the last place.

Check the actual fixed-point handle, circle centre slot and raw
coordinate bits. Verify each portable value using its own
projection. [Exact supplemental proof](../../../../../../re/solidworks/measurements/2026/SdkEndConditionCentreReadback01.json)
