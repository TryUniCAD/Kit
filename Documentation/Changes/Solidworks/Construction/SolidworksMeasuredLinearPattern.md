# SOLIDWORKS measured local linear pattern

Kit constructs the editable ordinary part history for a bounded oblique
linear pattern. The input owns two distinct rectangular Front profiles with
four axis relations each, a forward blind plate and joined raised seed, a
finite Top/Right hinge, an acute angular plane, and one signed linear pattern.
The final solid contains two through eight disjoint raised instances wholly
inside the plate. It retains the two stock depths, plane angle, instance count,
and spacing as editable dimensions. The measured stock sketches use
horizontal and vertical relations and have no sketch dimension parameters.

Submit a complete neutral part to the normal SOLIDWORKS SDK writer. When
exact source presentation matters, add the typed `PatPresentInput` in
`values["solidworks_pattern_presentation"]`. Its views, labels and parameter
IDs belong to the actual source geometry and are independent of native
measurement. Exact strict cold readback already carries this presentation
and can regenerate the part without an override.

The existing `solidworks_native_measurement` option still owns publication.
The pattern lane uses an envelope with `written_at` and a `receipt` containing
the exact matching `packet` and `result` JSON bytes. Each pair binds the
entire regenerated archive, including its self locator, before any
destination receives bytes. The two cases have separate measurements
for classic zlib and Windows zlib-ng.
The shipped LF result JSON and the original Windows CRLF result
authenticate the same exact observation.

Both disclosed cases passed clean native SOLIDWORKS 2026 SP05.2 open,
rebuild, spacing edit, save and fresh reopen, bracketed by two healthy
controls. Fresh SDK processes reproduced their complete archive hashes in
the direct writer, public registry and strict cold readback republication.
They recovered the linked plan, selected body owners, annotation presentation
and matching geometry without CAD runtime or input file reads. Design-only
strict reads retain the same typed feature and driver owners and can publish
the exact measured archive from a restored neutral JSON document. Both strict
read modes refuse a recognized cache-free pattern with incomplete typed
history. See the
[scope and reproduction record](../../../../re/solidworks/records/MeasuredLocalLinearPattern2026.md).
The [Windows compression trial](../../../../re/solidworks/records/MeasuredPatternCompression2026.md)
repeated those native observations and reproduced both alternate files
through the ordinary SDK and direct writer with the matching evidence.

Warm saves, alternate pattern modes, overlapping instances, and outputs
with new file digests remain outside this publication scope. This includes
Kit-authored edits to held values and compression variants that have not
completed a fresh native measurement.
The [adapter guide](../../../Reference/Adapters/Solidworks.md#measured-local-linear-pattern)
describes caller options and the destination boundary.
