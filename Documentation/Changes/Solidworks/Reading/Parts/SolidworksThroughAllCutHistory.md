# Read through-all cut history

The public SOLIDWORKS 2026 part reader preserves a forward, reverse, or two-direction through-all cut on the measured single mid-plane stock profile. It binds the actual stock depth, sketch geometry, consumed stock atom, and result body. The neutral cut definition stores `through_all` for each active end, with absent lengths and no cut depth parameter.

Create a geometric extrusion end with `ExtrusionFeature(end_condition="through_all")`. Set `second_end_condition="through_all"` for the other direction. Blind, mid-plane and two-length modes require a primary length. Existing serialized lengths retain their values.

Six disclosed native states pass strict path and byte reads, including independent stock depth edits. All six diagnostic mutations fail the typed path. The [process receipt](../../../../../re/solidworks/measurements/2026/PublicThroughAllEndRead01.json) and [field record](../../../../../re/solidworks/records/PublicThroughAllRead2026.md) report source identities and measured scope. Cold through-all geometry generation and held-out writer acceptance are separate verification work.
