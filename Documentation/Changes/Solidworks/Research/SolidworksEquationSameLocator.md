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

[Frozen procedure and scope](../../../../re/solidworks/records/WidthDepthSameLocator2026.md)
