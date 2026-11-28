# Stored dimension text is a three-dimensional point

The child sketch entities may be planar while their distance-display text has a nonzero normal coordinate. The actual owner is embedded `moDimText_c.f38` at `moDisplayDistanceDim_c.f6a0`; its ordinary serializer stores and loads three doubles. The four disclosed original height dimensions retain a saved Z of `0.0001 m`, although their source author requested Z zero. This observation does not establish an automatic layering constant.

Native `moDimText_c::setPosition` copies the complete point. For the concrete ordinary distance display, `SetTextPos` excludes its two ordinal-sort branches and leaves placement caches alone. The private research operation therefore preserves explicit XYZ after the qualified XY placement, then emits the complete graph through shared SDK codecs. It does not flatten source Z or fill it from another document.

A generic COM annotation origin is a separate API measurement and may describe an annotation attachment or text-box border. The [controlled native readback](../../../../../../re/solidworks/records/DrawingSpatialTextLifecycleProtocol2026.md#measured-lifecycle) verifies both owners through save and reopen.
