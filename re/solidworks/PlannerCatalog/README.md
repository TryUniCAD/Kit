# SOLIDWORKS planner catalogue

`Data/Catalog.sqlite` is the primary indexed planner input. `Data/Manifest.json`
binds provenance, exact counts, canonical content and artifact hashes. CSV exports
provide readable API types, members, parameters, constants, command candidates,
feature families, subfeatures, typed relationships and unresolved gaps.

Read the [collection and query guide](../../../Documentation/Reference/Research/SolidworksPlannerCatalog.md).
Run `VerifyCatalog.py Data` before consuming a saved bundle.

The curated plan lists 68 families and 585 subfeatures across nine dependency-aware
research waves. It uses 2026 official help as a discovery baseline. The installed
snapshot is executable `33.0.0.5050`, core type library `33.0`; those are separate
version boundaries. Every authoring, decoding, writing and verification status
remains `unverified`. This research inventory does not participate in production
conversion or qualify CAD support.
