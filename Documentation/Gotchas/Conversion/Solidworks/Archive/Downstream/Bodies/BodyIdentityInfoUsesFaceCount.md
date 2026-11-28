# Body lookup registration uses the current face count

When the optional `f90` row is added, its companion `f400` lookup record takes the current number of face rows at `uniqueIdInfo_c.f08`. The appender separately returns the ordinary zero-based body row ordinal.

Derive the count from the generated face collection and pass the actual body and representative face identities. [Source and packed clock](../../../../../../../re/solidworks/records/DownstreamBodyRepresentative2026.md)
