# Sketch attribute field order differs from the Design callback

## Expectation

The same native sketch-tag value uses one field order in every serialized form.

## Actual behavior

The ASCII string inside `sketch_attrib_def` stores primary identity, secondary identity, direction, topology role flags, split sequence, and split total. The binary Design callback instead stores version, primary identity, secondary identity, direction, split sequence, split total, and topology role flags.

The ASCII fourth word was previously described as an inserted zero, and the final pair as enumerations. Native stream operators show that all three words belong to the sketch-tag value. All observed role flags happen to be zero; 456 corpus attributes have non-default split pairs.

## Workaround

Map each wire form to named semantic fields rather than sharing an unqualified positional tuple. Use unsigned 64-bit domains for primary/secondary identities and role flags, unsigned 32-bit domains for direction and split fields, and validate the one-based fragment relationship. Keep unsupported nonzero role flags guarded until their complete meanings are qualified.

[Native instruction and corpus evidence](../../../../re/Fusion/Reconstruction/EntityGraph/SketchAsciiSemantics.json) records the exact offsets and overloads. [The production model change](../../../Changes/Fusion/FusionSketchAttributeSemantics.md) describes API migration and archive coverage.
