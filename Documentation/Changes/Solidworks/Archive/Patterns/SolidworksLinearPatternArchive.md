# SOLIDWORKS local linear-pattern archive readback

The internal SOLIDWORKS 2026 part codec reads ordinary local linear patterns in a linked Config-0 and ResolvedFeatures pair. It retains the actual seed, datum direction, selected stock lineage and separate number and length parameters. The two count displays use typed binary64 cache cells alongside their independent integer parameters.

The disclosed D01X and D02Y originals and their separate spacing and count derivatives reproduce all twelve linked streams exactly. Both existing controls reproduce four more streams. The scope excludes other shape selectors, populated skip and matrix objects, dimension override branches and alternate contexts. The existing public generic pattern and native writer eligibility are unchanged. [Evidence and command](../../../../../re/solidworks/records/LocalLinearPatternTypedArchive2026.md)
