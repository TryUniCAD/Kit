# Creo writer gap

## Current result

The adapter can replay a retained Creo source byte for byte.
It cannot author a new PSB part from a neutral model.

This is not a complete Creo writer.
The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) require a live feature tree, a solid body, measured volume and centre of mass, and a dimension edit that rebuilds.
None of those conditions is met for generated output.

## Why source replay is not enough

Source replay proves that the container and source digest survive a round trip.
It does not prove that Kit understands the authored records.
A neutral edit cannot be expressed by replaying the old bytes.

## Missing work

1. Decode the tagged field transition cache and the field table for `AllFeatur`, `FeatDefs`, and `FeatDefsDtm`.
2. Decode the geometry prototype lanes and the contour and topology references in `VisibGeom`.
3. Map feature identity, parent links, dimensions, relations, and configuration overrides to the neutral model.
4. Prove which derived sections Creo recomputes after a feature edit.
5. Build a symbolic writer that recomputes every index, count, checksum, and derived section.
6. Measure a generated part in a fresh Creo process between healthy controls.
7. Change a driving dimension, rebuild, and measure the geometry change.

## Next measurement

The next useful experiment is a one-feature ladder authored in Creo:

- a rectangular sketch on the default top plane;
- a blind extrude with one depth;
- the same part with a second depth;
- the same part with a second feature.

The ladder localises the feature record, the sketch record, the depth parameter, and the body reference.
The result must be recorded here before any writer field is promoted.

## Status

`vendor_loadable = False`
`application_usable = False`
`lossless = False`
`parametric = False`
