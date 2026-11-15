# Explicit SOLIDWORKS oracle interfaces

The curve-source authoring tool now loads the registered 2026 type library before querying child interfaces.
It resolves line, arc and feature wrappers from that library.
It uses each class's default interface directly.
It queries that interface on the returned object's raw dispatch pointer before constructing its generated wrapper.
For sketch mutation, it obtains the unique 2D sketch history feature from the new document's feature traversal.
It does not assume a fixed feature position or use the sketch's queried dispatch object for renaming.
The recorder also supports keyword arguments for the explicit library loader.

The previous automatic cast failed in both native controls when their returned objects rejected `GetTypeInfo`.
The [binding gotcha](../../../Gotchas/Conversion/Solidworks/Tracing/ExplicitTypeLibrariesForChildInterfaces.md)
records the failure and the explicit-library workaround.
The [raw-pointer gotcha](../../../Gotchas/Conversion/Solidworks/Tracing/GeneratedWrappersNeedRawDispatchPointers.md)
records why a dynamic wrapper cannot be passed directly to the generated wrapper constructor.
The [feature traversal gotcha](../../../Gotchas/Conversion/Solidworks/Tracing/SketchFeatureMutationNeedsDocumentTraversal.md)
records the native name-assignment failure after a successful interface query.

The command syntax is unchanged.
Each worker records the selected library identity and the requested interface binding.
Generated wrapper code stays in the guest's cache.
No vendor wrapper code is added to the repository or the production adapter.

Verification inspected the installed pywin32 implementation and the registered library without starting a CAD process.
The library reported version 34.0 and exposed the required wrappers.
Static syntax checking passed without importing repository code.

The corrected source preflight then passed ten fresh-process phases on SOLIDWORKS 2026 SP05.2, executable version `34.5.2.0604`.
The [source preflight report](../../../../re/solidworks/measurements/2026/CurveSourcePreflight.json) records the tool revision, source hashes, process identities and selected API results.
Both controls passed before and after the two selected discovery cases.
All 119 numeric checks passed.
All 16 measured snapshots had one body, zero feature errors and zero feature warnings.

| API-authored source | Driving edit | Baseline volume, m3 | Edited volume, m3 |
| ------------------- | ------------ | ------------------- | ----------------- |
| `ControlRectangle` | Depth `7.713` to `8.25291` mm | `3.982056093639e-6` | `4.26080002019373e-6` |
| `ControlCircle` | Diameter `22.346` to `24.80406` mm | `3.024912395655374e-6` | `3.726994562686987e-6` |
| `D04CircleRadius` | Radius `7.391` to `8.64747` mm | `2.013220351695231e-6` | `2.755897339435601e-6` |
| `D13Arc180Ccw` | Depth `7.139` to `8.49541` mm | `4.365715715744759e-6` | `5.195201701736263e-6` |

Each source reopened in a separate process before its driving edit and rebuild.
The recorded source hashes remained unchanged after verification because the edited documents were closed without saving.
The batch selected two discovery cases and generated no held-out native inputs.
Its parent exit code `2` denotes the expected incomplete selection.
The report records `locked=false`, `incomplete_selection=true` and `first_failure=null`.

These documents were authored by the SOLIDWORKS API.
No Kit-written curve output was measured, and no curve writer implementation exists.
The complete family lock and curve writer acceptance remain pending.
