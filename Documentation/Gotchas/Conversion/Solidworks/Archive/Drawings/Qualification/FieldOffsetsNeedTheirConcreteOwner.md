# Field offsets need their concrete owner

An integer field named `f08` does not universally identify a native feature. The generic archived drawing guard observer labeled edge-reference `f08` values as persistent IDs, but `moEdgeRef_c` inherits the `moBEntRef_c` entity-array count at that offset.

Bind each field to its concrete class, serializer and actual accessor or consumer. Keep the drawing's persistent node ID, the detailing map's downstream kernel ID and the reference object's entity count separate. Preserve the historical observation and record a semantic correction instead of rewriting its original source or report.

The [exact correction](../../../../../../../re/solidworks/records/DrawingRootGuardFieldLabels2026.md) compares the archived label with the independently measured typed entity count and pins the native count/array consumer. The new typed detailing accessor does not use the historical generic label.
