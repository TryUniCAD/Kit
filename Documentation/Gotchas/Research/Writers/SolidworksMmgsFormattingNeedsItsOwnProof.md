# Matching MMGS codes can conceal format differences

The Author04 source and the generated exact-sketch candidate both store millimetre length and the MMGS unit-system code in the typed `f9b8` table. The source length precision is two decimal places. The recipe uses four, and it also creates an MKS analysis table where the source has an absent `f9c0` reference.

Check formatting and the analysis-table reference separately when claiming source parity. The two MMGS codes confirm the unit family. Full native `GetUnits` reporting needs its own observation. [Source-matched offline comparison](../../../../re/solidworks/records/VendorBlindBossExactSketchPresentation.md#replay-the-captured-configuration-name)
