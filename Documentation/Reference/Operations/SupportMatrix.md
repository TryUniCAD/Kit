# Supported formats and conversion evidence

## Scope and revision

This matrix records production source at `1619f00bf532caad262d1557bd69281179e5c497`, inspected on 2026-11-27.
It consolidates existing contracts rather than introducing another planner or capability API.
The [backlog](../../Maintenance/ConversionBacklog.md) owns implementation tasks and dependencies.
The [roadmap](../../../Roadmap.md) owns milestone order.

Read and write registration is separate from acceptance of a particular document.
Every native output claim must meet all [CAD success criteria](CadSuccessCriteria.md).
A successful decode, retained source archive, or capability flag does not establish editable conversion.

## Reused planning records

| Existing record                                                         | What it supplies                                                             | What remains separate                                                                            |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| [SOLIDWORKS planner catalogue](../Research/SolidworksPlannerCatalog.md) | Feature families, subfeatures, dependencies, research axes and explicit gaps | Its qualification fields remain unverified; catalogue presence does not mean implemented support |
| [Fusion planner catalogue](../Research/FusionPlannerCatalog.md)         | Build-bound API declarations, native schemas and capture provenance          | Declaration availability and codec coverage do not qualify conversion                            |
| [Automation register](../Research/AutomationSteps.md)                   | Research ownership and revision-bound evidence                               | Completed jobs do not establish accepted conversion directions                                   |
| [SOLIDWORKS corpus coverage](../../../re/solidworks/CorpusCoverage.md)  | Committed input coverage and reader/writer research boundaries               | Samples alone do not prove general feature support                                               |
| [Adapter discovery](../../../src/convert/api/ApiAvailable.py)           | Installed reader/writer metadata                                             | Metadata versions are not a complete vendor compatibility range                                  |

Reuse these records when extending this matrix.
Do not copy their full inventories or create another scheduling database.

## File types, versions and feature boundaries

“Unverified range” means no complete minimum/maximum vendor-version compatibility contract was established by this audit.
An observed build identifies evidence, not all versions accepted by a parser.
Unsupported families remain required development work.

| Family     | File types and production identifier                                                           | Version evidence                                                                          | Read boundary                                                                                                        | Write boundary and remaining gaps                                                                                                                                                                                                                                                                                                                                                                                               |
| ---------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SOLIDWORKS | `.SLDPRT`, `.SLDASM`; `solidworks.sldprt`, assembly alias `solidworks.sldasm`                  | Exact measured part builds `34.4.1.1011` and `34.5.2.0604`; broader read range unverified | Part/assembly interpretation with retained native state; opaque native definitions remain outside portable semantics | Bounded Front-plane loop of 3–64 straight segments and one blind boss, with exact offline receipt; sketch constraints/dimensions outside that profile refuse. Assembly writing unsupported. [Part contract](../../Changes/Solidworks/Construction/SolidworksMeasuredPartPublication.md), [build extension](../../Changes/Solidworks/Construction/SolidworksEncoderOracleBuild.md), [reader](../Adapters/Solidworks.md)          |
| Fusion     | `.f3d`; `fusion.f3d`, alias `f3d`                                                              | Native acceptance recorded on `2706.1.17`; broader version range unverified               | Strict qualified constructor, circular and rectangle graph contracts; partial inspection is a separate reader mode   | Parameter, circle, rectangle, cylinder, cuboid and frustum constructor profiles; exact native-state reconstruction under projection agreement. Arbitrary graphs, ordinary edited saves and general cross-format histories remain unqualified. [Public contract and measurements](../../Changes/Fusion/Adapter/FusionPublicAdapter.md)                                                                                           |
| FreeCAD    | `.FCStd`; `freecad.fcstd`                                                                      | Scoped witnesses on `1.1.4`; metadata `1.0` is not an audited vendor-version range        | Archive/object graph, implemented sketches, expressions, features and assembly mappings                              | Implemented native emission and retained routes have different contracts. Fresh extrusion attestation remains false in the scoped audited path; strict publication refuses it. Other families require independent qualification. [Adapter](../Adapters/Freecad.md), [initial-open witness](../../Changes/Freecad/FreeCadInitialOpenWitness.md), [attestation limit](../../Changes/Freecad/FreeCadInitialGeometryAttestation.md) |
| CATIA V5   | `.CATPart`, `.CATProduct`; `catia.v5`                                                          | V5/`V5_CFV2` container; release/service-pack range unverified                             | Bounded native interpretation and embedded neutral manifest recovery                                                 | Source reconstruction and generated neutral carriers do not establish editable native feature reconstruction. Full geometry/history and measured target acceptance remain open. [Adapter](../Adapters/Catia.md), [metadata](../../../src/convert/adapters/catia/Format.py)                                                                                                                                                      |
| NX         | Intended native types/version contract unresolved; no production identifier                    | Unverified                                                                                | Unsupported: no production adapter at this revision                                                                  | Reader, independent writer and native acceptance required; historical PR #115 is closed without merge                                                                                                                                                                                                                                                                                                                           |
| Creo       | Intended native types/version contract unresolved; no production identifier                    | Unverified                                                                                | Unsupported: no production adapter at this revision                                                                  | Reader, independent writer and native acceptance required; historical PSB PR #117 is closed without merge                                                                                                                                                                                                                                                                                                                       |
| Rhino      | Intended native types/version contract unresolved; no production identifier                    | Unverified                                                                                | Unsupported: no production adapter at this revision                                                                  | Define version/type scope, then implement and qualify reader/writer                                                                                                                                                                                                                                                                                                                                                             |
| AutoCAD    | Intended native drawing types/version contract unresolved; no standalone production identifier | Unverified                                                                                | Unsupported as a standalone family; Fusion drawing codecs are separate                                               | Define drawing/version scope and portable semantics, then implement and qualify standalone routes                                                                                                                                                                                                                                                                                                                               |
| Kit JSON   | `.json`; `interchange.json`                                                                    | Current neutral model/codec at the pinned revision; no CAD vendor version applies         | Typed `CadDocument` JSON; developer decode reports are a different envelope                                          | Neutral serialization, not native CAD acceptance. Retained native state remains subject to each destination's admission checks. [JSON contract](../Adapters/Json.md)                                                                                                                                                                                                                                                            |

The [production adapter directory](https://github.com/TryUniCAD/Kit/tree/1619f00bf532caad262d1557bd69281179e5c497/src/convert/adapters) establishes the absent families at this revision.
Intended extensions for those families must be chosen explicitly; none are invented here.
Version gaps remain B01 follow-up work until compatibility evidence defines the release promise.

## Bounded circular offset reader extension

The [offset-start reader](../../Changes/Fusion/Readers/FusionOffsetStartReader.md) adds strict SDK and CLI inspection of an identity-XY unconstrained circle followed by an untapered NewBody extrusion with positive two-sided distances and a signed OffsetStart parameter.
It preserves five distinct owned parameter roles and requires the existing current-body, journal, snapshot, geometry and mass proofs.
The initial 139-file replay admits 109 XY files and explicitly refuses 30 XZ/YZ files.
The returned graph remains read-only; this extension changes the source read boundary without expanding the write or directional conversion matrix below.

## Directional route matrix

Rows are sources and columns are destinations.
The same status applies to each file type listed for a family, subject to the narrower exceptions below.

- **B**: bounded reconstruction documented in the linked contract; not a blanket conversion claim.
- **S**: supported neutral serialization contract; not vendor acceptance.
- **U**: unverified complete editable route; registration or a bounded subcase may exist.
- **X**: unsupported in this production revision because an endpoint has no adapter.

| Source → destination | SOLIDWORKS | Fusion | FreeCAD | CATIA V5 | NX  | Creo | Rhino | AutoCAD | Kit JSON |
| -------------------- | ---------- | ------ | ------- | -------- | --- | ---- | ----- | ------- | -------- |
| SOLIDWORKS           | B          | U      | U       | U        | X   | X    | X     | X       | U        |
| Fusion               | U          | B      | U       | U        | X   | X    | X     | X       | U        |
| FreeCAD              | U          | U      | U       | U        | X   | X    | X     | X       | U        |
| CATIA V5             | U          | U      | U       | U        | X   | X    | X     | X       | U        |
| NX                   | X          | X      | X       | X        | X   | X    | X     | X       | X        |
| Creo                 | X          | X      | X       | X        | X   | X    | X     | X       | X        |
| Rhino                | X          | X      | X       | X        | X   | X    | X     | X       | X        |
| AutoCAD              | X          | X      | X       | X        | X   | X    | X     | X       | X        |
| Kit JSON             | U          | U      | U       | U        | X   | X    | X     | X       | S        |

SOLIDWORKS **B** covers only the receipt-bound part profile above; `.SLDASM` output remains unsupported.
Fusion **B** covers the public contract's reconstructed graphs, not all `.f3d` documents.
Both bounded contracts include neutral JSON transport of admitted state.
This does not qualify arbitrary JSON-to-native graphs or complete native-to-neutral semantics.
A **U** cell does not assert every input fails or that no writer exists.
It withholds complete route acceptance until source fidelity, target edits and held-out evidence are established together.

B02–B05 own the first SOLIDWORKS ↔ Fusion qualification.
B12 owns complete directional acceptance, including feature, version and application evidence for each promised route.
The [automation register](../Research/AutomationSteps.md#deterministic-encoder-work) records bounded encoder results and remaining whole-source admission.
B06/B07 own broader feature histories, assemblies, configurations and drawings.
B09 owns the missing production families.
All unassigned release-version gaps remain visible under B01 rather than becoming implied support.

## Open work and coordination

Remote state was refreshed on 2026-11-27.
These observations are ownership records, not current-head review or acceptance verdicts.

| Delivery                                             | Observed head                              | Scope retained by that delivery                                                                              |
| ---------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| [PR #368](https://github.com/TryUniCAD/Kit/pull/368) | `f52ab1f00c2106bfb0e85ed0f3f2a1c0e9b5e9d2` | Open SOLIDWORKS feature/version census; reuse its table after accepted integration instead of duplicating it |
| [PR #366](https://github.com/TryUniCAD/Kit/pull/366) | `461272beaf3416f187821b817477395e1063cc01` | Open blind-boss offline preparation; does not supply the wider native milestone                              |
| [PR #299](https://github.com/TryUniCAD/Kit/pull/299) | `43b2a10c4bd3f02832b98404878be8c738ec1625` | Open saved-cuboid reader work; not production support at this baseline                                       |
| [PR #335](https://github.com/TryUniCAD/Kit/pull/335) | `fe88dd7b7ad4a16d4a1f00a7f4645920bea0107e` | Open P03 public-admission evidence; refusal evidence does not qualify a route                                |
| [PR #121](https://github.com/TryUniCAD/Kit/pull/121) | `6cf4d8a9ec216fdb82a873f5fffd3f2aa48d586b` | Open generative SOLIDWORKS research; preserve its reader/writer ownership                                    |

Historical [PR #115](https://github.com/TryUniCAD/Kit/pull/115), [PR #116](https://github.com/TryUniCAD/Kit/pull/116) and [PR #117](https://github.com/TryUniCAD/Kit/pull/117) are closed without merge.
They are not active production adapter deliveries.
Refresh replacement ownership before starting new format work.

## Maintain the matrix

1. Pin the inspected production revision and the exact acceptance evidence.
2. Read installed metadata and the corresponding adapter contract.
3. Link feature/version details to the existing catalogue or owning register.
4. Record read, write and directional acceptance separately.
5. Preserve unsupported and unverified cells when evidence is missing.
6. Refresh linked PR state before claiming work.
7. Update the backlog owner, delivery and exit evidence with each scoped change.

This audit used source inspection and remote PR metadata only.
It ran no decoder, CAD application, conversion, integration test or user evaluation.
It changes no runtime admission policy and promotes no native acceptance claim.
