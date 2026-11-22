# SOLIDWORKS measured local linear pattern

Kit constructs the editable ordinary part history for a bounded oblique
linear pattern. The input owns two distinct rectangular Front profiles with
four axis relations each, a forward blind plate and joined raised seed, a
finite Top/Right hinge, an acute angular plane, and one signed linear pattern.
The final solid contains two through eight disjoint raised instances wholly
inside the plate. It retains the two stock depths, plane angle, instance count,
and spacing as editable dimensions.

Submit a complete neutral part to the normal SOLIDWORKS SDK writer. When
exact source presentation matters, add the typed `PatPresentInput` in
`values["solidworks_pattern_presentation"]`. Its views, labels and parameter
IDs belong to the actual source geometry and are independent of native
measurement. Exact strict cold readback already carries this presentation
and can regenerate the part without an override.

The existing `solidworks_native_measurement` option still owns publication.
The pattern lane uses an envelope with `written_at` and a `receipt` containing
the exact `packet` and `result` JSON bytes. The immutable disclosed native
packet matches each entire regenerated archive, including its self locator,
before any destination receives bytes. The current results cover
`ColdRaisedPatternA` and `ColdRaisedPatternB` only.

Both disclosed cases passed clean native SOLIDWORKS 2026 SP05.2 open,
rebuild, spacing edit, save and fresh reopen, bracketed by two healthy
controls. Fresh SDK processes reproduced their complete archive hashes in
the direct writer, public registry and strict cold readback republication.
They recovered the linked plan, selected body owners, annotation presentation
and matching geometry without CAD runtime or input file reads. See the
[scope and reproduction record](../../../../re/solidworks/records/MeasuredLocalLinearPattern2026.md).

Warm saves, alternate pattern modes, overlapping instances, and compressed
variants with a different file digest remain outside this publication scope.
The [adapter guide](../../../Reference/Adapters/Solidworks.md#measured-local-linear-pattern)
describes caller options and the destination boundary.
