# Native part feature lookup is declared on IPartDoc

A native part document can expose `FeatureByName` through its actual COM dispatch while also supporting `IModelDoc2` methods. Requiring every observed method on `IModelDoc2` is an incorrect metadata preflight.

The pinned registered 2026 type library declares `FeatureByName` on `IPartDoc`, DISPID `5`, with one `VT_BSTR` name and a `VT_DISPATCH` result. `EditSketch` belongs to `IModelDoc2`, DISPID `65649`, with no arguments and a void result. The point setter belongs to `ISketchPoint`, DISPID `13`, with three double coordinates and a Boolean result.

Bind each prerequisite to its actual declaring interface and retain the already correct part dispatch. The misplaced owner stopped the perpendicular source protocol before CAD activation; it did not establish a native point-placement or mate failure. Host source fingerprints cannot substitute for checking the registered interface owner.

[Exact registered probe and preserved attempts](../../../../../../re/solidworks/records/PerpendicularMateSourcePosition2026.md)
