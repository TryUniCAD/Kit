# Typed datum aliases retain native owners

On the typed read path, a generated local-import part's reference planes
use keyword kind `Plane` and its origin uses `Sketch`. Their binary classes
remain `moRefPlane_c` and `moOriginProfileFeature_c`. A filter that expects
the class name as the public kind rejects the real local body even when
its partition and import feature agree.

Accept the two known kind, class and tag combinations when the concrete
resolved owner has a persistent ID and recorded offset. This keeps ordinary
sketches and other native feature classes outside the scaffold check.
Three independent disclosed generated imports retain byte-identical
16-stream outputs, and the renamed-body control retains its owned label.
[Aggregate readback](../../../../../../re/solidworks/measurements/2026/AggregateLocalImportReadback01.json)
