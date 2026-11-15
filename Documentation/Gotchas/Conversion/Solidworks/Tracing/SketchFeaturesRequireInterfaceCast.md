# Sketch feature casts do not guarantee mutation

## Expected

An `ISketch` object exposes a `GetFeature` method for obtaining the feature used
for naming and extrusion selection.

## Actual

The official 2026
[sketch segment example](https://help.solidworks.com/2026/English/api/sldworksapi/Get_Names_of_Sketch_Segments_Example_VBNET.htm)
declares separate sketch and feature variables, then assigns the sketch to the
feature interface. It does not invoke a sketch `GetFeature` member.
The initial curve source authoring wrapper used that nonexistent member.
The [installed 2026 type-library inspection](../../../../../re/solidworks/v2026/evidence/CurveAuthoringTypeLibrary.json)
confirms that `ISketch.GetSketchSegments` exists and `ISketch.GetFeature` does
not in the same hash-bound library. Its first native preflight stopped earlier
at the preference binding, so no later native failure is claimed.

## Workaround

The proposed interface-query workaround was later exercised on both source controls.
The query succeeded, but writing the returned feature's name failed with the native read-only-property error.
A successful interface query therefore does not establish mutation support through that dispatch object.

Use the [document traversal rule](SketchFeatureMutationNeedsDocumentTraversal.md)
to obtain the actual history feature before naming or selecting it.
`IFeature.GetSpecificFeature2` retrieves the specific sketch interface from that feature.
