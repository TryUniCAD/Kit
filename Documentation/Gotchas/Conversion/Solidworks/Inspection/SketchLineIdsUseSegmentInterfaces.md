# Sketch line IDs use segment interfaces

`ISketchLine` validates the concrete line interface but does not expose the
`GetID` method owned by `ISketchSegment`. A successful QueryInterface to
`SketchLine` does not make every method on the original segment dispatch
available through that generated Python wrapper.

The first disclosed SDK rectangle dimension observation converted each returned
relation entity to `ISketchLine` and then called `GetID` on that wrapper. All four
candidate attempts opened without errors or warnings and failed at this member
lookup. Neither dimension edits nor saves occurred. Both controls passed.
This is an observer interface failure and supplies no solid or edit acceptance.

Use the existing `CurveAuthor.entity_binding` path on the original returned
entity. It verifies `GetType` and the concrete line/point interface, while segment
identity remains on the original segment dispatch. Keep the resulting concrete
kind check and the exact relation/entity IDs; do not remove identity coverage.

The failed result SHA-256 is
`f59993896427905065daf9220da8efd1a69a8da17f9329073f45f89a0ed389b5`.
The [sanitized failure receipt](../../../../../re/solidworks/measurements/2026/SdkRectangleDimensionObserverFailure01.json)
records the source and evidence boundary. A retry must bind the unchanged failed
packet and generated inputs; an existing authored native path can be reused only
at the exact previous candidate hash and size.
