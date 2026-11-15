# Explicit SOLIDWORKS oracle interfaces

The curve-source authoring tool now loads the registered 2026 type library before querying child interfaces.
It resolves line, arc and feature wrappers from that library.
It uses each class's default interface directly.
The recorder also supports keyword arguments for the explicit library loader.

The previous automatic cast failed in both native controls when their returned objects rejected `GetTypeInfo`.
The [binding gotcha](../../../Gotchas/Conversion/Solidworks/Tracing/ExplicitTypeLibrariesForChildInterfaces.md)
records the failure and the explicit-library workaround.

The command syntax is unchanged.
Each worker records the selected library identity and the requested interface binding.
Generated wrapper code stays in the guest's cache.
No vendor wrapper code is added to the repository or the production adapter.

Verification inspected the installed pywin32 implementation and the registered library without starting a CAD process.
The library reported version 34.0 and exposed the required wrappers.
Static syntax checking passed without importing repository code.
The corrected native preflight, complete family lock and curve writer acceptance remain pending.
