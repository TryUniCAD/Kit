# A drawing-visible component is not the model root

Expecting IView.GetVisibleComponents to return the linked part's unit root is wrong for the measured ordinary Front view. Both pristine native controls returned IsRoot=false while resolving the correct physical part and authored view configuration. The observer failed before parent/model or edge calls; no candidate launched.

The native producer prepends a drawing-view reference chain and constructs the component in that context. Its root predicate differs from the independent model unit component. Keep the actual IView child, physical hash and configuration as distinct identity owners. The bounded retry requires a false root predicate, no assembly parent, exact empty occurrence configuration and an identical actual part model with the expected active configuration; it does not accept arbitrary parent/configuration combinations.

See the [source checkpoint](../../../../../../../re/solidworks/records/DrawingProjectionOccurrence2026.md) and [retained negative observation](../../../../../../../re/solidworks/measurements/2026/DrawingProjectionRootObserverNative01.json). The retry must prove the remaining parent/model predicates and complete annotation lifecycle before generated output is measured.
