# Late binding requires typed part selection arguments

The SOLIDWORKS API expects a null component for part-level extrusion selection.
The late-bound Python call sent an untyped `None` and returned a type mismatch.
The same installed build also refused `CreatePoint` through dynamic dispatch
while the sketch's native transform data was available.

Pass the null component as `VT_DISPATCH`. Use the documented native transform
array for world coordinate measurement and refuse invalid or scaled frames.
The base feature can report false for `IsBossFeature`; use `IsBase2` to identify
the native extrusion that creates the body.

The initial failures were measured on SOLIDWORKS `34.4.1` with the pinned P03
rectangular stock control. The [dispatch gotcha](DispatchResultsCanBeCallable.md)
describes the separate ambiguity for members without arguments.
