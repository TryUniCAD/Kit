# Fusion model parameter names vary with allocation order

Two strict saved cuboids place width, depth, extrusion distance and taper at `d4`, `d5`, `d6` and `d7`. Two other saved cuboids label those same roles `d6`, `d7`, `d2` and `d3`. The fixed-corner sketch and three independent size drivers are present in both cases. Treating `d6` as a fixed width or height key changes a parameter's meaning.

Resolve the horizontal and vertical dimension parameters through their sketch operands and owner links. Resolve extrusion distance and taper through the selected extrusion. Preserve the observed names, expressions, units, values and table order in the [saved binding request](../../../../../Changes/Research/Encoder/FusionSavedParameterBindings.md). Allocate the native IDs from the generated object graph.

The table's `children` references carry the logical order. Reordering the authored entities after their IDs were allocated caused the lower writer to refuse decreasing primary offsets. Set the table order through its references, preserving the emitter's physical entity order.
