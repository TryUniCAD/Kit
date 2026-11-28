# SOLIDWORKS saved linear-pattern read

The ordinary SOLIDWORKS 2026 part reader can project the measured saved single-direction pattern as a neutral linear-pattern feature. It follows the actual seed and selected local datum, and takes pitch and count from the live driving parameters. The same saved solid, topology IDs and native payload remain available. The reader binds the solid to its final atom and derives volume and centre of mass from its saved faces.

Six disclosed native saves pass the before/after SDK process comparison. The raw and no-B-rep routes retain their existing behavior, and variants outside the profile retain the generic reader. Native writing for this family remains unavailable. [Evidence and scope](../../../../../re/solidworks/records/LocalLinearPatternNeutralRead2026.md)
