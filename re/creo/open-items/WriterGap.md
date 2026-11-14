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

## One-feature ladder result

The first rung is authored and retained at `re/creo/oracle/ladder/ladder1.prt.2`.
It is a rectangle on `TOP` extruded as a solid with the default blind depth.
The paired empty control is `re/creo/oracle/empty/solid_start_part_mmks.prt`.

The ladder adds `FeatDefs`, `MdlRefInfo`, `IdsGenAllRepsDb`, `IdsGenSimpRepDb`, and `SldRegenRevInfo`.
`AllFeatur` grows by 4360 bytes and `VisibGeom` grows by 2868 bytes.
Those two sections are the next decode targets.
The section diff and the `DispDataTable` compression anomaly are recorded in
[the oracle notes](../oracle/Oracle.md).

## Next measurement

The next useful experiment is the second rung of the ladder:

- the same rectangle and extrude with a different depth;
- the same part with a second feature.

The second rung separates the depth parameter from the feature and sketch records.
The result must be recorded here before any writer field is promoted.

## Status

`vendor_loadable = False`
`application_usable = False`
`lossless = False`
`parametric = False`
