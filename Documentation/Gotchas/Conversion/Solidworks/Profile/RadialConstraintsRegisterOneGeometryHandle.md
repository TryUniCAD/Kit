# Radial constraints register one geometry handle

## Expectation

A circle dimension contains two embedded geometry handles.
Both handles could appear to contribute a geometry reference or constraint-map entry.

## Observed behavior

The 2026 circle dimension's actual geometry-count virtual returns one.
Its geometry accessor returns `h1` at runtime `+0x130`.
The optional map therefore registers only that handle.
The second embedded handle is not a second registration for this class.

The retained radial creation path separately increments the original arc's geometry count exactly once.
Value-array append and temporary cleanup do not add another increment in the recorded fresh path.
That geometry count is separate from the dimension's lifetime count and the map descriptor's attachment count.

## Workaround

Follow the concrete dimension's geometry-count and accessor virtuals.
Count actual geometry reference operations separately from handle copies and map entries.
Use the [arc-reference record](../../../../../re/solidworks/records/ArcDimensionReferences2026.md)
for exact dispatch, cleanup and serializer evidence.
Later deletion, block handles and dirty-map rebuilds require separate rules.
