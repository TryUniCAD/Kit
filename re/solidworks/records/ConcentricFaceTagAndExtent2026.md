# Concentric face tags and cylinder extents in SOLIDWORKS 2026

Fresh native writer acceptance remains pending. This separate follow-up explains the last-resolved face tag and inherited surface tuple without using the disclosed saved numbers as construction defaults.

Task `B04-SW2026-MATES-CONCENTRIC`; owner `/root/flag_ownership`; delivery PR #121. Dependencies are the [actual kernel identity domains](ConcentricKernelFaceIdentity2026.md), the [support snapshot producer](ConcentricSupportSnapshotConstruction2026.md), actual occurrence placement and root's disclosed D01–D03 kernel audits. Exit for this tranche is a native publication rule for `moFaceRef_c.f70` and a guarded ordinary two-rim cylinder extent rule, with numerical and lifecycle limits retained. It changes no SDK, schema, builder or public support boundary.

[Numeric proof](ConcentricFaceTagAndExtent2026.json) binds thirteen complete functions, fifteen instruction windows, seven direct calls, one complete tail-jump instruction and four RTTI-verified primary tables. Original `sldmodu.dll` build `34.5.2.0604`, machine `0x8664`, preferred base `0x4b140000`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` supplies every address in this record. Complete extents follow the declared exception directory and chained unwind records. Original instruction bytes were decoded statelessly; vendor listings and bytes remain outside the repository.

## Last-resolved face tag `f70`

`moBEntRef_c` constructor `[0x4b748310,0x4b7483f4)`, SHA-256 `bb5173015c86225fe1dcee5fc99b68fde6dd49263e58be93dd4fc183a1d1ef1d`, initializes its runtime `+0x70` eight-byte slot to null at `0x4b748365`. Actual `moFaceRef_c` constructor `[0x4bc11630,0x4bc11b7a)` calls that base and installs the concrete primary table `0x4cf95ed0`. It creates actual surface identities and, on its ordinary resolution branch, calls the resolver at `0x4bc119c5 → 0x4bc12cc0`.

The resolver `[0x4bc12cc0,0x4bc1371d)`, SHA-256 `7904ed5c2cf96e9e70c2d6c03f588af24d9946d169e215abdabd211a27c5536a`, has two relevant publications:

- At `0x4bc12d9b`, after a non-null cached entity passes imported `gcTopEnt_w::identity == gcTopEnt_w::faceType`, it writes that actual face handle to `this+0x70` and returns the same handle
- At `0x4bc136dd`, after surface-identity resolution and actual-body cache publication, it writes the selected non-null face handle to `this+0x70`, then returns that handle

The named `moFaceRef_c::getFace2` `[0x4bc12b40,0x4bc12cbe)` independently has the same valid-face publication at `0x4bc12bc8`. The actual concrete serializer dispatch calls `moBEntRef_c::Serialize` at `0x4bba9669 → 0x4bba3780`.

That base serializer `[0x4bba3780,0x4bba41ef)`, SHA-256 `e5491d90050bf64fd704e55ddf869319cc680b69a3a3559bb7e3d8827ff90c07`, writes `+0x70`'s low unsigned-32 value at `0x4bba3852–0x4bba385e`. From version `1175`, the load branch reads an unsigned-32 word and zero-extends it into the eight-byte runtime slot at `0x4bba3a56`. Ordinary `19000` takes that layout.

The field therefore represents the last actual resolved kernel face handle/tag, in a runtime pointer-like slot. It is separate from the persistent face `node_id`, archive object/map index, transmitted index, feature ID and body atom ID. **Confirmed**: native publication and wire width, corroborated by the actual disclosed graph. The separate kernel allocation/packing rule is not recovered by this publication trace. No universal face-tag allocation offset is established.

Root's immutable `FaceTagCorrelation01.json` SHA-256 `8b02d46eb0bcdf568980236c488e0bd90b64fedb3a3e5f3ce3d2b1140bbed2d3` compares all twelve endpoints to their actual six child states. The low sixteen bits agree with the actual lateral `SWEntUnchanged` high word. The six states also have a face-tag/body-match difference of `32`. Those are corroborating observations, not an allocation algorithm. Root's separate `CapOrdering01.json` SHA-256 `6eded807678ef6549608cec4b331cb00305a52b2d7aaa3f882a8668463fdaf42` preserves actual lateral loop/cap order and its two null entries. Both reports were independently rehashed; no saved tag or cap array is fed to a constructor here.

A fresh constructor-null tag is an explained native state, not yet an oracle-proven neutral replacement for a fully resolved saved selection. A generator must either carry its actual model-derived kernel handle/tag or explicitly keep the unqualified cold state for a controlled native experiment. It must not compute `BODY_MATCH + 32` from this corpus.

## Inherited surface tuple `fb0/fb8/fc0/fc8`

The concrete cylinder constructor `[0x4c3073c0,0x4c3074f2)` initializes the shared surface tuple to `(-1, 1, 1, -1)` at `0x4c3073f6–0x4c307426`. This is actual constructor code before the concrete cylinder table is installed, not an inferred saved tuple.

`moSurfaceRef_w::Serialize` `[0x4c2797d0,0x4c27994c)`, SHA-256 `0c232ded7e8488beeb43b932066ec6bfe0e8480fa73ff073f9023b280081393b`, stores four doubles in order `fb0`, `fb8`, `fc0`, `fc8` from version `3875`; current load reads the same sequence. Older load initializes the constructor tuple and omits those doubles. Ordinary `19000` is the measured modern layout; no legacy qualification is transferred.

Concrete cylinder slot `+0x3d0` points to the complete five-byte tail jump `0x4c3297e0 → 0x4c3299f0`. Its full target is `[0x4c3299f0,0x4c32a82f)`, SHA-256 `94c97b216d2c7a8c8d143e59bfd93b6c725363f288ee2ca8ad1cfd6ba848de8b`. The constructor's update path calls that virtual slot at `0x4c325c2b`; `getCylinder` can call it at `0x4c314013` under its actual refresh condition.

The common target has explicit guards:

1. The wrapper must be an actual cylinder or cone wrapper
2. Imported `gc_isGhostingEnabled` must return nonzero at `0x4c329a75`
3. Component types `moCompRefCylinder_c` and `moCompRefCone_c` are explicitly excluded at `0x4c329aa6–0x4c329ade`
4. The component must be an actual `moCompFace_c`, resolve a non-null face, and that face must be cylindrical or conical

The detached support cylinders under `f3c8` therefore exit this update before geometry traversal. Their unchanged `(-1,1,1,-1)` tuple is explained by the actual support constructor and exclusion. This is distinct from the active face-backed wrapper.

## Selected ordinary two-rim cylinder operation

For the real cylindrical face, the helper gets its actual edges through `gcFace_w::getEdges`. For each circular edge it obtains native radius, center and axis through `gcEdge_w::getCircleData`, transforms center and unit axis by the actual occurrence transform, requires the radius difference to be at most `1e-8`, and requires parallel axes. It projects an accepted center onto the actual cylinder line using `mgLine_c::pointPerp` and retains distinct axial support points. Native point comparison uses the `-1` default-tolerance sentinel; this record does not invent a new distance threshold.

On the bounded ordinary full cylinder with exactly two distinct circular rims, both accepted centers give axial points `Q0` and `Q1`. Let `P` and `A` be the actual wrapper's world cylinder root and unit axis. The remaining publication computes displacement vectors from `P`, their native squared lengths and direction relative to `A`. If one displacement passes the native null-vector test and the other is non-null, the path writes:

`fb0 = 0`

`fb8 = signed_norm(other_axial_point - P, A)`

The sign is positive in the same direction and negative in the opposite direction. This is a geometric distance after occurrence transformation and projection, not the authored depth copied into a cache and not a global-Z comparison. It explains why occurrence-specific saved values can differ in the last floating-point bits from the neutral depth. Full native arithmetic/IEEE bit identity is not claimed.

At `0x4c32a1da` this cylinder path loads the existing `fc0/fc8`. Actual cylinder type excludes the separate cone handling at `0x4c32a242`. The final stores `0x4c32a6ee–0x4c32a710` write the two calculated axial values and the retained secondary pair. Thus a fresh ordinary cylinder retains constructor `fc0=1`, `fc8=-1` through this selected update. No generalized angular meaning is assigned to those two fields without its own accessor/consumer proof.

**Confirmed**: constructor tuple, exact serializer order, component exclusion and the selected native operations, corroborated by all twelve disclosed active/support pairs. **Partial**: model-generated execution of this rule, native ghosting/refresh scheduling in a fresh candidate, floating-point equality, non-two-rim cylinders, both axial points away from the root, partial circles, fallback bounding-box mode and cone branches. Those cases do not inherit the simplified formula.

## Custody and next measurement

The disclosed graph remains SHA-256 `5a28338afa61c3b71daa0059970321e8134b3ace275ebc6f3f36dac0fef8ce4b`. In all twelve endpoints, active `fb0` is zero, active `fb8` is positive, active `fc0/fc8` retain `1/-1`, and the detached support retains the whole constructor tuple. The exact graph/path evidence is carried in the JSON supplement. These rows are research evidence only.

The narrow next native check is the already planned complete generated cylinder assembly, with explicit actual child geometry and face/atom IDs. Record active versus support tuple ownership separately before rebuild, after rebuild and after save/fresh reopen. Compare the active signed extent with the actual transformed rim geometry; retain the ghosting/refresh guard as an unresolved scheduling condition if it is not observed. Do not substitute a saved field or change the existing `f108` presence policy silently.

No VM, CAD, COM, hidden input, local schema/codec test or shared source mutation occurred. No Hopper session was opened. Root owns actual qualification and publication. Full C1–C11 acceptance remains open; the governing stopping conditions are “The first is success under every criterion on this page.” and “The second is the end of the available context.”

[Tag-domain gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Assembly/Mates/FaceReferenceTagsAreResolvedKernelHandles.md) · [Change entry](../../../Documentation/Changes/Solidworks/Construction/Assembly/SolidworksConcentricFaceTagAndExtent.md)
