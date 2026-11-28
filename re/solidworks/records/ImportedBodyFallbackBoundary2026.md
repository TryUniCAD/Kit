# Generated imported-body and capability-loss boundaries

Task `B04-SW2026-IMPORTED-BODY`, PR [#121](https://github.com/TryUniCAD/Kit/pull/121). This offline audit pins the implementation to `ed8058f74238dfb84cb328d4bebf0bd4336197cd`. Its inputs are tracked source and sanitized receipts. [Owning register](../../../Documentation/Maintenance/ConversionBacklog.md) · [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Generative writer phase](../../Playbook/WriterModel.md)

## Reachable model-only construction

`write_document(document, path)` reaches `SldprtWriter.supports` and `PlanImportPart` for a document with a typed `BrepModel`. This profile needs a part path, millimetres, one active root configuration and one bare boundary. `PrepareImport` computes the final locator, creation event and ambient light. `MakeBareImport` dispatches the typed topology to `MakeLocalPrism` or `MakeLocalCyl`, then frames and compresses the new local transmit through `EncodeLocalBody`. The encoder validates the resident graph, current terminal-fin schema and canonical node indices. Its inputs are model nodes and a key. [Writer selection](../../../src/convert/adapters/solidworks/Core/Writing/SldprtWriter.py) · [Plan](../../../src/convert/adapters/solidworks/Core/Preparation/Imports/PlanImportPart.py) · [Preparation](../../../src/convert/adapters/solidworks/Core/Preparation/Imports/PrepareImport.py) · [Part composer](../../../src/convert/adapters/solidworks/Archive/Construction/Part/Imports/MakeBareImport.py) · [Typed encoder](../../../src/convert/adapters/solidworks/Archive/Partition/LocalWrite/EncodeLocalXmt.py)

The smallest qualified positive is one axis-aligned box with two distinct coordinates per axis and their eight exact Cartesian corners. Each of the six faces needs its own axis plane at the linked ring's exact coordinate. The compiler validates one untransformed solid region with an outward closed shell, one ordered outer trim per face, analytic plane and line carriers and two opposite finite uses per edge. A same-count trapezoid, a triangle, a foreign loop or an off-station face refuses. A second profile covers a canonical periodic cylinder. Its closed mantle and two outward caps must share the signed axis, radius and linked full circular rims. A valid generic B-rep, an open shell, a tolerance-bearing trim, an arbitrary spline surface, or geometry available only as an opaque payload supplies insufficient evidence for these compilers. [Box guard](../../../src/convert/adapters/solidworks/Core/Preparation/Imports/CheckImportGeo.py) · [Prism compiler](../../../src/convert/adapters/solidworks/Archive/Partition/LocalPrism/MakeLocalPrism.py) · [Cylinder scope](../../../src/convert/adapters/solidworks/Archive/Partition/LocalCylinder/ReadCylShape.py) · [Host contrasts](../../tooling/sw2026/imported_body_source/VerifyPublicBox.py)

## Physical owner and exact native evidence

The recognized SOLIDWORKS 2026 SP05.2 archive uses `moBaseBody_c` schema 1 and archive version 19000. Its `sldmopartu.dll` wrapper at `0x1802fcb70` calls the import serializer at `0x1802fd060`. The modeled suffix is a source-filename CString, signed route word, local storage key CString and signed mesh-segment count followed by its rows. The generated route emits an empty filename, the local switch `1`, the feature-derived key and an empty mesh vector. [Exact static owner](ImportedBaseBody2026.md) · [Linked typed grammar](ImportedBaseBodyTypedLayout2026.md) · [Import field definitions](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/ImportFields.py)

The root `fd88` manager and feature `f528` share the allocated atom. The feature's `f498` stores the generated atom ID. Its `f3d0` and the root `fe38` bind the selected and activation marks to the independent body-free `Contents/Config-0-Partition`. The feature's key addresses its one `Config-0-FeatureBodies/LocalBodies` group. The strict reader checks the actual group against the resolved owner and reconstructs the complete boundary. It attaches the single returned B-rep body to the design body. A separately authored body label has its own native owner. [Feature binder](../../../src/convert/adapters/solidworks/Archive/Construction/Part/Imports/BindImportMut.py) · [Strict local read](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/ReadLocalBodyBrep.py) · [Design body link](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/LinkLocalBody.py) · [Body names](SdkImportedLocalBodyNames2026.md)

Both normal SDK trials used `sldworks.exe` version `34.5.2.0604`, SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`. Each exercised four distinct native processes, two healthy controls, clean candidate rebuild and a separate save and fresh reopen. Both report exactly two native transfers, `brep` and `configurations`. The rectangular receipt records zero runtime input reads. The periodic observer requires zero construction input reads before writing the build lock bound by its native receipt. The commits below are ancestors of the audit pin. [Periodic publication guard](../../tooling/sw2026/imported_body_source/ObservePublicCyl.py#L189)

| Disclosed scope | Writer revision and generated file SHA-256 | Receipt SHA-256 and native checks |
| --- | --- | --- |
| Translated rectangular solid | `93c0174353bdc7a4cd3dd155b2ba40066ac96483` · `e1a6a5428030ee336a7b03657bcf4d30f28c350497b81ecc3e7243063928f268` | `fa2fd1cb268aed0e202ec135ecd2e7792180e822795c4ea2de3e9fd377b15d2c` · 116 checks. [Receipt](../measurements/2026/SdkPublicRectangularNative01.json) |
| Oblique periodic cylinder | `8adcfeee894815e45380618aac3fea6eacb6d631` · `120d5ef09767aa1180bcfbf3c6818331594d53ab0a5091cebfb625080803361f` | `7d18092bcf71dc7a10ef179eb9016c0eb56486ea495b4569eaddbb7e8008588c` · 152 checks. [Receipt](../measurements/2026/SdkPublicPeriodicNative01.json) |

The related research composer completed four disclosed plane/line lifecycles, including concave prisms, and the SDK then read all eight candidate and saved parts with 40 exact linked-stream re-emissions. The concave evidence stays in that narrower research route. A later bare rectangular regression compared two previously locked sources and passed both geometry and saved-read checks after re-adjudication. It records zero new independent cases, whole-source conversions or original FCStd conversions. [Completed native parts](../measurements/2026/GeneratedLocalBodyPartCompleted01.json) · [Typed readback](../measurements/2026/ImportedLocalBodySdkSavedRead01.json) · [Paired geometry regression](../measurements/2026/SdkSealedBareRectangleNative01.json)

## Intact source, loss accounting and next evidence

`ReadBareModel` refuses design bodies, feature timeline, sketches, parameters, selections, payloads, metadata and other owners. `ReadBareConfig` refuses overrides, suppression and extra configuration state. `PlanImportPart` also refuses original file identity. A full source entering through the registry hits `supports` during implicit selection, or the explicit validation gates. `CheckNative` refuses opaque `NativeFeature` definitions and unresolved required semantics. An opaque definition identifies a decoding or transfer boundary. It supplies no authority about whether a native SOLIDWORKS parametric equivalent exists. [Bare document](../../../src/convert/adapters/solidworks/Archive/Construction/Part/Imports/CheckBareImport.py) · [Bare configuration](../../../src/convert/adapters/solidworks/Archive/Construction/Part/Imports/ReadBareConfig.py) · [Registry write](../../../src/convert/adapters/registry/RegistryWriteApi.py) · [Native semantics gate](../../../src/convert/adapters/registry/NativeWrite.py)

`EmitNativeMut` reports exactly the two native transfers for an admitted bare import. `WritePolicy.CheckTransfers` checks declared and inferred source capabilities. Any nonempty `WriteResult.dropped` or missing required transfer raises `CapabilityLossError` before staged publication, including when `allow_carrier` is enabled. Geometry-only input already lacks the omitted owners, so its empty `dropped` set cannot describe a conversion from the intact source. C3 requires whole-source preservation and C4 requires editable target geometry for a parametric source. [Import result](../../../src/convert/adapters/solidworks/Core/Writing/EmitNativeMut.py) · [Write policy](../../../src/convert/adapters/base/WritePolicy.py) · [Carrier option gotcha](../../../Documentation/Gotchas/Conversion/Registry/CarrierOptionPreservesRequiredCapabilities.md)

The existing `ProjectDisclosedImport` diagnostic is the closest source-linked experiment. It keeps the source read-only, establishes the sole final design body and actual `moBaseBody_c` and configuration owners, compares exact signed box incidence, and lists omitted source domains. Its parametric extrude control refuses. [Existing projector](../../tooling/sw2026/imported_body_source/ProjectDisclosedImport.py) · [Source projection evidence](ImportedBodySourceGeometry2026.md)

The two independently locked baked FreeCAD sources each bind a literal `Part::Feature` to its verified `Shape` payload and empty authored dependency set. Kit's FreeCAD writer can also create `Part::Feature` as a shape carrier with a `ParametricSource` link. Admission therefore needs the native links and typed owners, complete oriented incidence and mass properties, and an account of each omitted source capability. A source carrying editable intent needs its actual native mapping or a separately authorized lossy contract. [Baked source custody](BakedFcstdSourceEligibility2026.md) · [FreeCAD source classification](../../../src/convert/adapters/freecad/Native.py#L1954) · [FreeCAD shape carrier](../../../src/convert/adapters/freecad/Archive.py#L6297)

## Baked box orientation and local tolerance

Two disclosed strict SDK reads preserve the actual associated design body, a reversed shell use and one reversed face use. The guarded projection uses their typed coedges and shell orientation to compare all six outward rings against the common rectangular builder, including direction and cyclic incidence. Both ring inventories match exactly. The independent live primitive control is refused by the imported-feature ownership gate even though it also has rectangular geometry.

Each disclosed source assigns `1e-7` mm to the six faces, twelve edges and eight vertices. The model-only transmit experiment converts that supplied length to meters and fills the explicit typed tolerance field in each of those 26 local nodes. All other decoded fields match the ordinary generated transmit, and each populated transmit re-emits byte for byte. The guarded projection and serialization recorded zero runtime accesses. Both generated parts pass the native lifecycle. Their saves retain all six exact face values and use the missing sentinel for edges and vertices. Effective tolerances and the original source provenance and appearance transfers remain open. [Uniform tolerance proof](../measurements/2026/DisclosedBakedLocalTolerance01.json) · [Reproduction tool](../../tooling/sw2026/imported_body_source/ProveBakedLocalTolerance.py) · [Complete part and native save packet](BakedLocalToleranceNative2026.md)

## Exact measured planar publication

The aggregate route on base `908b9dddbdd7d3978bbf544e9a75d45000148e82`
previously routed imported geometry to the plain receipt parser. It
also required a filesystem path during selection and only qualified
rectangular or periodic geometry in model preparation. The focused
port uses the authenticated local-import receipt from
[PR #259](https://github.com/TryUniCAD/Kit/pull/259) at
[`e6a83ad0`](https://github.com/TryUniCAD/Kit/tree/e6a83ad0204253dfb977fad503f9659a8aa77829).
The known
[completed native report](../measurements/2026/GeneratedLocalBodyPartCompleted01.json)
has SHA-256 `40d77a01a37e8d85517fbfa642a208bdcd3b29378d426021b643cbd909e1a6c4`.
It binds the two bracket controls, 11 distinct native lifetimes and the
source, rebuild, save and reopen record identities on SOLIDWORKS 2026
SP05.2 `34.5.2.0604`.

| Authorized case | Complete archive SHA-256 | Size | Native checks |
| --- | --- | ---: | ---: |
| `RectangularBare` | `302c8e9b608e513a714ef3139c5f4fcc4e8033fedf4718b6591f4a2aff80a357` | 9,914 | 116 |
| `ConcaveOwned` | `fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33` | 10,890 | 164 |

The exact self locators are
`C:\KitImportedProbe03\Candidates\RectangularBare.SLDPRT` and
`C:\KitImportedProbe03\Candidates\ConcaveOwned.SLDPRT`.
The explicit creation event is `1790000000`. The scoped rule first
validates the canonical report, then commits the regenerated bytes
only after the size and full digest match. The **source** helper
`ReadBareModel` still refuses authored feature history, unknown
metadata and original file identity. The **result** reports the
`sldprt.parametric_history_unavailable` diagnostic alongside the two
native transfers. It asserts no missing requested capability for the
geometry-only neutral input.

The rectangular profile retains the original unattributed BODY.
The concave profile requires an orthogonal six-corner loop with one
reflex corner, one exact carrier plane per face and the fully validated
outward prism. Its BODY attribute list takes the feature name and
persistent ID from the generated `moBaseBody_c`, its atom ID from the
shared typed Config-0 and ResolvedFeatures graph, and its stamp from
the same creation event in both headers. The body proof observes
`ATOM_ID_2001=101`, `LAST_BODY_MODIFYING_FEATURE_ID=18`,
`ENT_TIME_STAMP_2001=102`, the actual Unicode name and the empty recipe.
Existing `CheckOwnedXmt` validates the linked node list, definitions and
values before serialization. The older `ConcaveBare` report slot,
periodic model-only preparation and wider or edited outputs are outside
this publication authority.

Both guarded standalone verifiers from the #259 pin were run against the
aggregate. Each report was **byte-identical** to its prior tracked host
receipt. Direct and registry streams preserve all 12 streams per case,
one active configuration and the exact body and feature association.
The separate signed-ring integration measures 2,574 mm³, 1,150 mm²
and (−2.5, 14, 8.5) mm for the rectangle, and 5,160 mm³, 2,068 mm²
and (17.441860465, −4.302325581, 3.5) mm for the L prism. Strict
design-only reads retain the same producer and body link. Both
processes report zero runtime input events and preserve all rejected
stream and filesystem targets. The unchanged Skew and Step
parametric archive digests agree.

| Evidence at the pinned #259 revision | SHA-256 |
| --- | --- |
| [Rectangle host report](https://github.com/TryUniCAD/Kit/blob/e6a83ad0204253dfb977fad503f9659a8aa77829/re/solidworks/measurements/2026/SdkMeasuredRectangularImport01.json) | `f5052cec97e37c7fab8fde82db35aa6231a429f9c2a45d8d7ec40d359b5e0b01` |
| [Concave host report](https://github.com/TryUniCAD/Kit/blob/e6a83ad0204253dfb977fad503f9659a8aa77829/re/solidworks/measurements/2026/SdkMeasuredConcaveImport01.json) | `5cea29c5f2b6e79f21a6cfa483a034c7bfa7b7b70fe81235b59b7540018ed4fc` |
| [Rectangle Windows paths](https://github.com/TryUniCAD/Kit/blob/e6a83ad0204253dfb977fad503f9659a8aa77829/re/solidworks/measurements/2026/SdkMeasuredRectangularImportWindows01.json) | `44ffcda1e8d91576f840bfd09eb8e2e67f673d84c9aa1f91f51bd8e3e5af0870` |
| [Concave Windows paths](https://github.com/TryUniCAD/Kit/blob/e6a83ad0204253dfb977fad503f9659a8aa77829/re/solidworks/measurements/2026/SdkMeasuredConcaveImportWindows01.json) | `41e72c645ac46ef03e98d49d098dc6e73a7512e38211138cb97cf6cb634ff386` |

To reproduce the host result from the aggregate checkout, put the
pinned `VerifyMeasuredBox.py`, `VerifyMeasuredConcave.py` and
`ConcaveImportCase.py` from `re/tooling/sw2026/imported_body_source/`
in a fresh scratch directory. Their respective source SHA-256 values are
`0e823c96b074dac076454e2b9db0da21c2d464d4ea61e6675fb3f75c091d2f30`,
`a14c6741782e8f11ef2563b73bfa722f8437b685309a86f534e96d3b77c019a3`
and `d24fe34ce8a186d36a1e20b530ab5eed8b6520772e8e79b1ab3d31fed66a65c7`.
In the scratch copy of `VerifyMeasuredBox.py` set `ROOT = Path.cwd()`.
From the aggregate checkout run both verifiers in separate
`python3.12 -I -B` processes with classic zlib. The proof ran on Python
3.12.14 and checked the unchanged output of both verifiers. Python
3.14.7 independently matched each candidate, publication and strict
read. Current work added zero native lifetimes, zero new held-out
cases and zero intact-source or FCStd conversions.
