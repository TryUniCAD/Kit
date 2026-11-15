# Explicit type libraries for child interfaces

## Expectation

`win32com.client.CastTo` could appear sufficient to obtain every sketch interface from a returned COM object.

## Observed behavior

Both 2026 curve-source controls failed during automatic casting.
The rectangle failed at `SketchLine` and the circle at `SketchArc`.
Their returned objects had no generated class identity.
Automatic casting tried `EnsureDispatch`, whose `GetTypeInfo` call failed with `Invalid index`.
That failure does not prove that the requested interface is unavailable.

## Workaround

Load the registered 2026 type library explicitly before casting child objects.
The oracle authoring tool uses library `{83A33D31-27C5-11CE-BFD4-00400513BB57}`, locale zero, major version 34 and minor version zero.
Generate its wrappers eagerly, resolve the requested class and its default interface, then construct that wrapper around the returned object.
The wrapper performs the interface query without discovering the child object's type library.
Keep generated wrappers in the guest cache, outside repository checkouts.

The installed pywin32 implementation and its [upstream source](https://github.com/mhammond/pywin32/blob/main/com/win32com/client/__init__.py)
explain the automatic discovery branch and wrapper construction.
The installed registered library exposed the required line, arc and feature wrappers.

The corrected [source preflight](../../../../../re/solidworks/measurements/2026/CurveSourcePreflight.json) passed ten fresh-process phases on executable version `34.5.2.0604`.
Its recorded line and arc interface queries returned raw `PyIDispatch` objects through the explicit version `34.0` library.
Both controls and both selected discovery sources passed authoring, reopening and edit checks.
All 119 numeric checks passed, with one body in every measured snapshot.
This verifies the selected source-authoring binding path.
The complete family lock and acceptance of Kit-written curve output remain pending.
