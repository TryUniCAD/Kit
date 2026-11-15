# Public FreeCAD assembly acceptance

Status: source acquired and hash-locked; conversion and application acceptance
are unfinished. There are no completed FreeCAD/SOLIDWORKS comparison screenshots
at this revision.

The user requires a large, independently published FreeCAD project, conversion
of its assembly and parts into native SOLIDWORKS, and actual screenshots from
both applications embedded in the PR description. The description must link the
original CAD source so the result can be independently reproduced.

## Locked source

Selected project: [GA3D-basicbot-2023](https://github.com/GA3Dtech/GA3D-basicbot-2023),
published by Alain David Geiser / [GA3D.tech](https://project.ga3d.tech/).
The publisher distributes the design under CERN-OHL-W-2.0 and provides a separate
[copyright notice](https://github.com/GA3Dtech/GA3D-basicbot-2023/blob/41b36c5fe9050f0e5a23e95d7ae8d9aa6d298bec/Copyright.txt).

The complete native root is
[`900a_GA3DtechProject_v1.0.FCStd`](https://github.com/GA3Dtech/GA3D-basicbot-2023/blob/41b36c5fe9050f0e5a23e95d7ae8d9aa6d298bec/900a_GA3DtechProject_v1.0.FCStd).
It is 42,616,942 bytes with SHA-256
`053bdb3235269a95735cb2746b4588b1c8007a3330edce406cf1c2868b77da7d`.
The publisher revision is `41b36c5fe9050f0e5a23e95d7ae8d9aa6d298bec`.

All 68 native documents plus the publisher's license, copyright, README and
disclaimer were acquired over HTTPS at that revision. Each downloaded file was
checked against its Git blob identity. The native documents contain 2,205
document objects in total, including 64 PartDesign bodies, 195 sketches, 74 pads,
129 pockets, 41 chamfers, 30 fillets, 34 holes, four additive pipes, patterns,
mirrors, Boolean features and reference geometry. These are counts across
source documents, not an assembly occurrence count. The root alone contains ten
component objects and 24 assembly-constraint objects. Its nested components
must be expanded before claiming a complete occurrence inventory.

The [lock manifest](../v2026/heldout/PublicAssemblyLock.json) records every path,
source URL, size, Git blob identity, SHA-256, object count and type inventory.
The unmodified files remain under the private research path
`.rescratch/sw26/public-acceptance/ga3d-basicbot/`. Source bodies and constraints
are not donor SOLIDWORKS data. Production writing must still compute every target
byte from source semantics and documented format rules.

## Required acceptance evidence

1. Open the unchanged root and all required dependencies in FreeCAD. Record the
   application build, source digest, complete component hierarchy, placements,
   features, constraints, body count and mass properties.
2. Capture the actual FreeCAD application with the complete source assembly and
   feature tree visible. Preserve the unedited screenshot and its digest.
3. Run Kit conversion without a CAD application or license. Emit native
   SOLIDWORKS parts, subassemblies and the root assembly. Record output hashes,
   generated-output counts, all capability losses and runtime-access audit.
4. Inspect generated documents in fresh SOLIDWORKS processes between healthy
   controls. Require zero load/rebuild errors and warnings, matched geometry to
   six significant figures, preserved feature/mate semantics, live dimension
   editing and a successful save/reopen. A screenshot alone does not pass these
   measurements.
5. Capture the actual SOLIDWORKS application showing the generated root assembly
   and its parts. Include both application screenshots directly in the PR
   description, with the original source page and immutable download link.
6. Keep missing parts, lost mates, baked parametric features, empty geometry,
   repairs, unhealthy controls and absent evidence as failures. Do not substitute
   the source publisher's image, a renderer or vendor-assisted conversion for
   the requested result.

## Source-selection record

The manufacturer-published LulzBot TAZ 6 root was also inspected. Its 14,085,416
byte file has 28 component objects and 47 constraints. It is retained privately
as a source-selection candidate; it is not the selected large-project lock and
has no conversion result. The GA3D project provides a larger complete native
source set with explicit publisher attribution and per-part parametric history.
