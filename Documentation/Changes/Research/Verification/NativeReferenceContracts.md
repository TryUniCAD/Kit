# Collect native origin and empty direction references

The SOLIDWORKS semantic collector now accepts a zero-coordinate point of type `User` or `Origin` when its independently verified sketch owner is the built-in `OriginProfileFeature`. SOLIDWORKS 34.4.1 returned `User` type 1 through both dynamic dispatch and the generated `ISketchPoint` interface for the P03 origin reference. Requiring only type 8 incorrectly left the origin constraint unmeasured.

The same build returned `-1` from `GetDirectionReference`, with both reference objects null and both reference-type outputs `-1`, for the ordinary sketch-normal extrusion. The collector accepts only the complete empty tuples for return values -1 or 0. It still rejects explicit references and inconsistent output tuples.

The private transport does not rewrite these vendor observations. Separate versioned collector sets let the repaired checkout be measured without replacing another job's default collectors. That personal service implementation remains outside this repository.

Live probes confirmed the origin coordinates and types and the complete direction output tuple. The P03 native measurement sequence opened, rebuilt, edited, saved, restored, and reopened all three driving dimensions between healthy controls. Full SOLIDWORKS semantic comparison remains unresolved; these corrections do not qualify its complete decoder output.

See [the native-reference gotcha](../../../Gotchas/Research/SolidWorksNativeReferenceValues.md).
