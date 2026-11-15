# Obtain the sketch feature through its interface

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

Query the same sketch object for its feature interface and record that cast as
a native phase. Fail closed if the installed type library cannot provide it.
Keep this separate from `IFeature.GetSpecificFeature2`, which retrieves the
specific sketch interface from an existing feature.
