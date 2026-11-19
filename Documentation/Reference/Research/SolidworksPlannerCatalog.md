<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS planner catalogue

## Purpose and scope

The collector produces an indexed SQLite inventory for research planning and CSV
exports for inspection. It follows the separation used by
[Fusion PR #163](https://github.com/TryUniCAD/Kit/pull/163): declarations, curated
planning records, provenance and unresolved evidence remain distinct.

The saved plan covers 68 families and 585 subfeatures. It includes sketch
geometry, relations and dimensions; reference geometry; solid, surface, direct
editing and pattern families; sheet metal; weldments and structure systems;
mold tooling; mesh and scan domains; assemblies and mates; motion; drawings,
views, dimensions, annotations and tables; MBD/DimXpert; materials,
configurations, equations and external references; interchange and optional
products. It records research axes rather than enumerating every legal option
combination. All support qualification remains `unverified`.

## Version-bound inventory

| Inventory                                   | Observed count |
| ------------------------------------------- | -------------: |
| Installed type libraries                    |             31 |
| Declared types                              |          3,282 |
| Function and property accessor declarations |         28,087 |
| Declared function/accessor parameters       |         43,084 |
| Variables, including enum constants         |         15,284 |
| Curated feature families                    |             68 |
| Curated subfeatures                         |            585 |
| Official taxonomy discovery sources         |             27 |
| Delivery waves                              |              9 |

The snapshot's executable version is `33.0.0.5050`; its core SldWorks type
library version is `33.0`. The curated plan uses 2026 official help. A matching
name across those sources does not establish cross-version availability.
The manifest gives exact final database counts and artifact hashes.

The saved database contains 94,299 items, 5,345 typed relationships, 60 sources
and 5,239 explicit gaps. Its feature plan includes 3,900 option research axes.
Of the gaps, 5,224 are references to ten external types outside the extracted
installation libraries; these remain unresolved rather than becoming invented
declarations. Command metadata contains 3,657 enum candidates.

## Collection and verification

Collection reads installed `.tlb` metadata with registration disabled. It does
not start SOLIDWORKS, attach to a user session, execute modelling commands,
create documents or copy vendor executables, type-library files, source code or
help prose. The saved snapshot contains independently extracted declaration
facts and provenance. The builder and verifier consume saved metadata offline.
Windows with `pywin32` is required only for fresh type-library extraction;
bundle construction and verification use Python's standard library.

For a fresh observation, point the collector at the licensed installation and
choose an unused snapshot path:

```powershell
uv run --with pywin32==312 python re/solidworks/PlannerCatalog/TypeLibrary.py `
  --install-root "C:/Program Files/SOLIDWORKS Corp/SOLIDWORKS" `
  --output $env:TEMP/SolidworksApiSnapshot.json
```

Run verification before querying a saved bundle:

```powershell
uv run python re/solidworks/PlannerCatalog/VerifyCatalog.py re/solidworks/PlannerCatalog/Data
```

Rebuild into a fresh destination using saved source metadata:

```powershell
uv run python re/solidworks/PlannerCatalog/BuildCatalog.py `
  --api-snapshot re/solidworks/PlannerCatalog/Sources/ApiSnapshot.json `
  --feature-plan re/solidworks/PlannerCatalog/Sources/FeaturePlan.json `
  --output $env:TEMP/SolidworksPlannerCatalog
```

Existing destinations are refused. Keep the proprietary installation outside
the repository. Use the collector's `--help` for fresh extraction arguments.
A new snapshot is a separate version-bound observation and must not overwrite
immutable campaign evidence.

For a fresh metadata snapshot, choose an unused output file:

```powershell
uv run --with pywin32==312 python re/solidworks/PlannerCatalog/TypeLibrary.py `
  --install-root "C:/Program Files/SOLIDWORKS Corp/SOLIDWORKS" `
  --output $env:TEMP/SolidworksApiSnapshot.json
```

## Saved interfaces

| Artifact                                | Planner use                                                       |
| --------------------------------------- | ----------------------------------------------------------------- |
| `Data/Catalog.sqlite`                   | Primary indexed inventory                                         |
| `Data/Manifest.json`                    | Source provenance, exact counts and artifact hashes               |
| `Data/ApiTypes.csv`                     | Installed interface, class, enum and other type declarations      |
| `Data/ApiOptions.csv`                   | Members, accessors, signatures and parameter metadata             |
| `Data/ApiEnums.csv`                     | Declared constants and their owners                               |
| `Data/Commands.csv`                     | Command candidates from enum metadata                             |
| `Data/Features.csv`                     | Curated families/subfeatures, options and acceptance scope        |
| `Data/Relations.csv`                    | Typed relationships and discovery links                           |
| `Data/Gaps.csv`                         | Missing evidence and unverified domains                           |
| `Data/NativeSchemas.csv`                | Explicit empty native-schema observation; COM is not wire grammar |
| `sources`, `items`, `relations`, `gaps` | Readable stable SQL views                                         |

Open SQLite read-only and query the documented named interfaces. For example:

```sql
SELECT kind, COUNT(*) FROM items GROUP BY kind ORDER BY kind;
SELECT id, name, details FROM items WHERE kind = 'feature_family' ORDER BY id;
SELECT * FROM gaps ORDER BY id;
```

The source plan retains the curated research axes, dependency lists, acceptance
criteria and official URLs. Parameter defaults and flags are declaration facts;
values absent from metadata remain absent. Enum constants are not legal-value
proof for every parameter of the corresponding underlying integer type.

## Coordinated delivery plan

Dependencies decide execution; wave labels express priorities. A solid sweep,
for example, depends on path/control-curve work even if that prerequisite's wave
is labelled surface. Keep one owner per research claim and serialize access to
any future shared CAD oracle.

| Wave          | Scope and exit gate                                                                                                                            |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Foundation    | Resolve units, identity, placement, reference ownership, state, materials and configuration dependencies                                       |
| Alpha         | Qualify the campaign's bounded editable basic extrusion first, retaining its live sketch, constraints, driving parameters and rebuild behavior |
| Solid         | Add bounded solid families with held-out and invalid cases; preserve topology and parameter dependencies                                       |
| Surface       | Preserve curve controls, continuity, supports and editable surface dependencies                                                                |
| Manufacturing | Prove fold states, manufacturing parameters, tool ownership and cut lists                                                                      |
| Assembly      | Preserve occurrences, transforms, configurations, external references, mates and degrees of freedom                                            |
| Drawing       | Preserve sheets, views, model associations, annotations and tables, including model-edit updates                                               |
| Extended      | Establish installed version, licence, external-data and API prerequisites for each optional product                                            |
| Strict        | Close every relevant native field, option, configuration and history state in an explicitly declared domain                                    |

Each feature's exit requires revision-bound source/output evidence, complete
ownership/reference semantics, meaningful distinctive and held-out cases,
invalid-input rejection, offline execution without donor bytes or CAD runtime,
target-application checks against healthy controls, a driving edit/rebuild/restore,
and separate bounded-alpha versus strict-lossless qualification. Geometry checks
include bodies, volume, centre of mass, topology and placement where applicable;
other domains require their own equivalent semantic measurements.

Do not use this curated denominator to replace campaign progress. Existing
bounded alpha receipts remain campaign-owned and are neither reset nor promoted
by a catalogue build. Strict fidelity includes native metadata and presentation
work deferred from the immediate editable alpha milestone.

## Gaps and interpretation

The catalogue is complete for the records it explicitly contains. It does not
claim universal SOLIDWORKS product, version or legal-combination coverage. COM
metadata does not expose the full native file grammar. Documentation discovery
is not runtime availability. Add-ins, third-party providers, command state,
units/ranges, method-specific enum subsets and cross-version behavior remain
explicit unresolved work. See the
[metadata availability gotcha](../../Gotchas/Research/SolidworksMetadataAvailability.md).

Task `SW-CATALOG` owns this inventory and its three research lanes. Programme
A03/A07/A08/A09/A10 and [PR #158](https://github.com/TryUniCAD/Kit/pull/158)
retain their delivery ownership; [PR #162](https://github.com/TryUniCAD/Kit/pull/162)
retains planner integration. This catalogue does not execute a scheduler,
implement a production writer or establish translation acceptance.
