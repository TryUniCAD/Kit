# Typed rectangle dimensions in SOLIDWORKS reading

The ordinary version-19000 SDK reader now consumes the actual two point-distance
drivers and four horizontal/vertical line relations of a qualified four-line
rectangle. Each distance retains both selected endpoints, its live named length,
and its actual dimension/display/parameter ownership. Source keyword values and
coordinate matching do not choose a relation's target.

Use the normal `open_document` API. Qualification requires concrete schema-one
classes, the same retained sketch alias in every display handle, complete local
handle references, matching geometry and parameter lengths, exact manager counts,
and entity reference counts derived from the actual relation graph. This extends
the [typed line-loop reader](SolidworksTypedLineLoopRead.md).

Empty managers retain the previous unconstrained polygon route. Extra relation
groups, other geometry, projected distances, tolerance/attachment modes and
unresolved owners do not gain the new typed classification. Other legacy sketch
behavior and public writer qualification remain unchanged.

An independently frozen SDK closure reads both disclosed generated originals and
all four native edited derivatives. All six expose four actual lines, six actual
relations and the two typed driving parameters. A separate comparison against
their prior native snapshots passes 252 numeric checks and all 36 relation
bindings. The independent process replay passes all fourteen phases across sixty
real workers. It includes three fresh neutral rectangles, equal driving values,
stale keywords, extended handles, seven malformed ownership/mode cases and the
unchanged polygon, circle, system-tree and legacy reader regressions. A prior
frozen attempt stopped at a missing tracked test dependency before any test ran;
the final source closure includes the exact disclosed dependencies and preserves
all 41 implementation/test/tool hashes.

The [research ledger](../../../../../re/solidworks/records/SdkRectangleTypedRead2026.md)
binds exact source, original measurement and read-result identities. The
[sanitized receipt](../../../../../re/solidworks/measurements/2026/SdkRectangleTypedRead01.json)
retains the six disclosed results. The
[reference-count gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Resolved/EntityReferenceCountsDoNotMeanExtraGeometry.md)
explains why nonempty constraint state must not be discarded or accepted by
loosening a geometry guard.
