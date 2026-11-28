# Sketch displays can include support-plane dimensions

Expected: the first display dimension returned for a named circle sketch is that sketch's radius.

Actual: the qualified 2026 Front-offset source returns `D1@OffsetPlane` first, then `D1@PlaneSketch`, when traversing `PlaneSketch`. This persisted with a freshly queried/cast `IFeature`, explicit registered method DISPIDs and a native/canonical identity check confirming the correct feature. The first dimension is linear type `2` and has the plane distance; the second is radial type `5` and has the circle radius. This evidence does not support blaming a stale Python dispatch wrapper.

Workaround: resolve the intended parameter by its actual feature-qualified name. Traverse the named feature's displays with a bound, check `FullName`, physical type and native object identity against that parameter, and require exactly one matching binding. Independently check the circle's actual radius. Neither a first-display position nor a numeric value alone establishes ownership.

The source author, distance edit and fresh reopen passed with `IsSame=1` and equal canonical `IUnknown` for the intended parameter/display pair. [Measured record and receipt](../../../../../../re/solidworks/records/ReferencePlaneDimensionOwnership2026.md). Scope is the disclosed ordinary offset-plane/circle source on SOLIDWORKS 2026 SP05.2; no broader traversal-order guarantee or generated writer acceptance is implied.
