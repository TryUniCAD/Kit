# An angular datum display owns its leader selection

The ordinary angular display writes the signed `ff80` index from `setForeshortenShiftedPoint` separately from the `ff68` point. Its arc direction and text radius come from different fields. Three disclosed saves write a zero index, and a fourth writes `16777215` with the same zero point. The constructor has no proved default for the index.

Supply the specific angle display's leader choice when composing its presentation. Preserve the shifted point's separate role and keep unknown shift semantics outside the bounded construction. [Owned setter, store and model contrast](../../../../../../re/solidworks/records/LocalLinearPatternAngularPlaneGraph2026.md#explicit-leader-input)
