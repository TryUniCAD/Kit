# Plan a verified FreeCAD origin box for SOLIDWORKS

The internal `PlanOriginBox` function accepts the strict neutral model of a
schema-four FreeCAD 1.0 or 1.1 part with one origin-fixed AdditiveBox. It
checks the physical Body and AdditiveBox shape lineage, the actual XY-plane
datum, identity placements, inactive attachment and three live length
drivers. The plan retains the intact source document and its 26 local
boundary roles beside the separately generated Front-plane part model.

Two disclosed FreeCAD 1.0.2 and 1.1.4 inputs reproduce the previously
native-tested files byte for byte through `MakeOriginBoxPart`. Six isolated
SDK processes verify the original payload owners, strict target readback,
zero guarded runtime file reads and the same seven pre-staging refusals on
each intact input. A same-map attached F14c source still takes the distinct
Top-plane projection. The public writer rejects the retained native
payloads, provenance and round-trip metadata before publication.

[Planner evidence and reproduction](../../../../../re/solidworks/records/FreecadF14aReferenceInputs2026.md#planner-and-remaining-transfer-contract)
[Exact offline receipt](../../../../../re/solidworks/measurements/2026/SdkFreecadF14aOriginPlan01.json)
