# SOLIDWORKS width-to-depth equation at one locator

The research preparer builds a plain part and a part with one width-to-depth
reference from the same neutral Alpha model. Both use the same encoded self
locator, geometry and chronology. Four guarded builds reproduce the two
outputs with zero construction reads. Their exact typed archive comparison
changes only Config-0 and its linked ResolvedFeatures.

The native procedure uses the same part observer and independently
calculated dimension and geometry bounds for both arms. It performs the
same driving width edit, measures its effect on the second dimension and
checks save and fresh reopen between two native controls.

The corrected observation passes both arms across six fresh native
processes. Editing the width to 47.875 mm keeps the plain depth at
19.5625 mm and drives the reference depth to 23.9375 mm. Both saved
derivatives reopen cleanly and preserve the measured geometry.

[Frozen procedure and scope](../../../../re/solidworks/records/WidthDepthSameLocator2026.md)
· [Native result](../../../../re/solidworks/measurements/2026/WidthDepthSameLocatorNative01.json)
· [Relation receipt representation](../../../Gotchas/Conversion/Solidworks/Oracle/Extrusion/RelationReceiptUsesJsonArrays.md)
