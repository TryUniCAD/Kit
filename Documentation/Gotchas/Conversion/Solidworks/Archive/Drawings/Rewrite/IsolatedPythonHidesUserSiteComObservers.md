# Isolated Python can hide an installed COM observer

The actual Windows Python 3.12 SDK import gate passed in isolated mode, but the first native control workers failed before any CAD process or record. Root's exact guest import-only probes identify `pythoncom` as unavailable in isolated mode. The same `Swapp` and `InspectDrawingCache` modules import in the existing legacy Python environment, without launching CAD.

The pure SDK generator keeps its isolated process. The native observer uses the previously qualified bytecode-suppressed legacy environment and explicit pinned tool directory. Run the passive observer import gate in that environment before the native batch. Retain all failed observations and reuse hash-verified generated inputs; do not classify a module-import error as a CAD file failure or a native crash.

[Measured setup failure and retry scope](../../../../../../../re/solidworks/measurements/2026/BlankRewriteObserverIsolation01.json)
