# Generated offset-plane native discovery

The first generated trial fails full feature-tree preservation: all four native phase snapshots pass with zero load errors or warnings, one body and the predicted geometry, but fresh reopening changes one unassigned-material caption. The aggregate result remains failed. The [sanitized receipt](../measurements/2026/GeneratedOffsetPlaneNative01.json) preserves this distinction.

Task `B04-SW2026-REFPLANES` is owned by `/root/assembly_occurrence`, delivered through PR #121 and depends on the shared Part, Model, Sketch, Extrude and radial constructors. This record covers the first generated Front-offset circle/boss, its distance edit and an independent persisted-field audit. The exit remains generated held-out open, edit, rebuild, save and fresh reopen between healthy controls. Angled and multiple-reference planes remain outside this profile.

## Frozen source and first native result

The [pre-writer native source lock](../v2026/heldout/ReferencePlaneSourceLock01.json), SHA-256 `c61560deff9c84addd65db48664ce6a5488ad3eecde9a070c62a215a5541d703`, predates the writer. Both hidden designs remain sealed. Writer revision `ebbfb4d8d4e7b888968c8197f37baf064b26060b` and all 3,879 source files in manifest `7491a46458bfd56f81acc93bbc6aebd58c8980df0cc5d18d2b03300d0f44ff0c` are frozen. [Construction rules](ReferencePlaneOffsetConstruction2026.md)

| Identity | SHA-256 |
| --- | --- |
| First native packet | `a43921209ef18d8a35ee31e12a17e2c9b7a1496bd90232dfae9e71137955f5f5` |
| Frozen observer | `4e4cf6bc4e2d9dfd807cbd6c00ec3376ca41b895c1579f8ba26df65d0c263cef` |
| Generated input, 8,638 bytes | `ccd77c5d0a0b1d870fdade39b50df5d14999866ba36e58286066cb5765f86cd6` |
| Raw final native result | `9ae09c539f93e399c73ff2c30802c42b9095650ed5904ed042e0fe6ecd5dd768` |
| Host transport, terminal exit `1` | `26dc605c80ed49540e5d06729c1f6a84c35c54e28efbbe6473466de339c8289b` |
| Native edited output, 60,180 bytes | `9d56fa06f2d80540ae232f165ef21795c3c67e70872e36b386f55a08b18a9ba5` |

The four fresh process identities comprise the disclosed Front control, generated input, edited saved copy and trailing disclosed control. Both controls pass and every input remains unchanged. Every phase opens with errors/warnings `0/0`. The generated part already has one body before the explicit rebuild. Its actual principal parent, `OffsetPlane`, `PlaneSketch`, `PlaneBoss` and driving dimensions all pass the native observer.

| Measurement | Initial | After plane-distance edit and fresh reopen |
| --- | --- | --- |
| Plane distance, m | `0.01789` | `0.02867` |
| Circle radius, m | `0.00973` | `0.00973` |
| Boss depth, m | `0.00531` | `0.00531` |
| Body count | `1` | `1` |
| Predicted volume, m³ | `1.5793197786817586e-6` | same |
| Predicted area, m² | `0.0009194763113044151` | same |
| Predicted centre of mass, m | `(0, 0, 0.020545)` | `(0, 0, 0.031325)` |

All measured volume, area and centre coordinates satisfy the frozen relative `5e-7` / absolute `1e-12` checks. The distance edit returns status `0`, rebuild succeeds and native SaveAs returns `[true,0,0]`. Fresh reopening repeats the edited geometry and driving values. These bounded results do not make the failed aggregate a pass.

## Exact tree failure and material ownership

Both generated snapshots contain 27 recursive feature rows. Only zero-based row `18` differs:

| State | Name | Type | Parent | Error / warning / suppression |
| --- | --- | --- | --- | --- |
| Edited live model | `authored material` | `MaterialFolder` | null | `0 / false / false` |
| Fresh reopened model | `Material <not specified>` | `MaterialFolder` | null | `0 / false / false` |

The [existing material construction record](MaterialFolderConstruction2026.md) already binds the native empty-material constructor to resource `0x4497`, the inherited name setter and English vocabulary `Material <not specified>`. The [existing gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/MaterialFolderNameChangesOnSave.md) records this same nonempty authored-title normalization on other generated parts. This is an additional instance, not a newly discovered general naming rule.

A fresh bounded original-PE check independently verifies the material constructor body `[0x4beae310,0x4beae3a8)`, SHA-256 `f203b52a0c8cdf3af76ade6cc860ffee137026c46d560536dfc6a66e74a7e5e7`, and the selected `sldresu.dll` resource block. Resource ID `0x4497` is block `1098`, entry `7`, language `1033`, payload RVA `0x1e0498`. All 2,288 block bytes are consumed under the sixteen-entry UTF-16 string-table rule; the payload SHA-256 is `ac8673a065e924a4514e8db2d26babd3063dc87b231d71886e6fb0c35389f2f2`. The private re-verification receipt SHA-256 is `9c460d4a7e531622267499c4a08a09282d02b0d09e3e5dd38341832a7aefbabe`. No vendor code or resource payload is redistributed.

The edited saved file still persists node name `authored material`, empty material string and current wire flags `0x80000000`. Its file hash is unchanged by fresh reopening while the live tree reports the resource caption. This corroborates the existing reopen/query boundary and rules out this first save overwriting the persisted caption. The higher-level rename caller remains untraced. Assigned materials, arbitrary authored-title preservation, other languages and other document kinds are not qualified.

## Independent typed saved-sibling audit

[AuditGeneratedReferencePlane.py](../../tooling/sw2026/serial/AuditGeneratedReferencePlane.py) verifies the frozen complete code closure, native result and exact generated/saved identities, then reads only those two disclosed native artifacts. Its private passing receipt SHA-256 is `65b5d4f4db97293710af7773d4d604333f486d37f118af291906c39c29a1614b`; audit tool SHA-256 is `fc0d96207f23567929f90dcc5fc6dda9e4048b1803e3ac824620588694df8ff7`. Twelve scoped stream round trips and two linked Config/Resolved re-emissions pass, together with eighteen graph/header/lifecycle checks and six edit-identity checks. The read guard records four native opens across exactly two files, zero denied events, zero packet writes and zero held-out reads. No CAD process starts.

| Typed owner/state | Fresh generated file | Native edited saved file |
| --- | --- | --- |
| Plane and dimension identity | generated IDs | unchanged |
| Selected principal and sketch support | actual local references | unchanged |
| `moFaceRefPlnData_c.f54/f58` | `-4/-4` | `1/2` |
| Inherited borders | four zeroes | `(0.010703,-0.010703,0.010703,-0.010703)` |
| Plane display `fad0`, m | shared constructor `0` | driving distance `0.02867` |
| Dimension optional axes/frame | absent / absent | present / present |
| Radial parameter/cache, m | `0.00973` | `0.00973` |
| Radial reference norm, m | `0.01789` | `0.02867` |
| Model, top and configuration update stamps | `101` | `156` |
| CMgrHdr2 configuration update | `101` | `156` |
| CMgrHdr2 geometry / transform stamps | `101 / 101` | `107 / 101` |
| Config map start / next | `4 / 83` | `4 / 121` |
| Resolved map start / next | `83 / 217` | `121 / 291` |

These are measured lifecycle observations. Native-saved presentation and cache values are not writer inputs. In particular, the border measurement does not establish a universal `1.1*radius` construction formula.

The first audit reused a native-saved display-cache assertion on the fresh generated state and returned a failed typed diagnostic, SHA-256 `6d9d632c93f263567f11f597390292ec428b0fdc8d0b3ffc2d2c58083c48f56c`. It is preserved. The revised auditor checks the already implemented shared constructor's explicit zero `fad0` before native saving, while retaining equality to the driving value after native saving. No writer, native artifact, tolerance or native tree assertion changes. Six enclosing raw load/store operations remain in the generated resolved stream; the saved files exercise additional raw operations. No complete field-classification claim follows from these scoped round trips.

## Native initialization edge for the fresh axis marker

Original `sldmodu.dll` SHA-256 is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The native face-plane alignment path obtains `fa4` through leaf `0x4b286330`; value `1` selects helper `[0x4c2e8b00,0x4c2e9054)`, SHA-256 `7bc8f6a8ff1c97eb32354d20a4e93ba40fbf17a4b10eb1f35cfae4de4e4ef454`. Within its guarded modern branch, `0x4c2e8c4d` tests `f54==-4`, and `0x4c2e8c62` calls axis initialization `0x4c2ebb70` with the actual referenced plane normal. That helper writes the resulting `f54/f58` at `0x4c2ebd9b` and `0x4c2ebd9e`; complete span `[0x4c2ebb70,0x4c2ebdbc)` has SHA-256 `5a8173eb00f08baece8091f30e84c5314a3b677037b4d80a470002927a03b14e`. This establishes an explicit construction-state initialization path, rather than a table of saved axis codes.

Its imported `gcVersion2012_a` guard resolves in original `sldgcu.dll`, SHA-256 `77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594`, to leaf `[0x43a81e10,0x43a81e1d)`, SHA-256 `940b5bbf75900d215f926829f2a3ddbe9d85bd0c271fe847d68e3bedbafa6017`. That leaf compares a signed geometry-version global at `0x4415bad0` against `0x6f`. The file-backed initial value is `305`; this is distinct from archive model version `19000`. Runtime overrides and the actual live guard value were not instrumented. The static edge is **partial** as an execution claim; the generated Front case's load/rebuild/save observations independently confirm the measured transition from fresh markers to saved axes. Other axis/context branches remain unqualified by this generated trial.

## Unmodified-code semantic retry

A second independently generated packet changes only the neutral unassigned-material caption to the pinned English resource vocabulary and moves the encoded output path to new immutable custody. It changes no writer or observer source and retains the exact full-tree equality gate. Two fresh guarded builds produce identical 8,671-byte files, SHA-256 `3e051c5639f5c8797e6ec39860e50c433b252e28af421999737eeb033f647f27`, with eleven round trips per build and zero runtime input reads.

The second packet SHA-256 is `13d2595920eefd54b5e323f5ad179f3c46aee32797605b7d3293ec7a66a93501`; transport recipe SHA-256 is `a8c6f53aa5794c2d19755bb372207dcda266d011a46d055e01c92b4b6621f34e`. Host verification passes without CAD. The failed first result is not rewritten, arbitrary material labels are not silently normalized by Kit and no captured cache is inserted.

## Second disclosed native result

The [second native receipt](../measurements/2026/GeneratedOffsetPlaneNative02.json) passes the unchanged aggregate: four distinct native processes, zero load errors/warnings, both healthy controls, immutable inputs and the complete identical 27-row generated/edit/reopen tree. The exact geometry and driving-distance edit in the table above pass again, and SaveAs returns `[true,0,0]`. The material caption is now `Material <not specified>` in both the generated live tree and fresh reopened tree. This is acceptance of the exact disclosed Front-offset candidate and its edited derivative, not qualification of the whole reference-plane family.

| Second-trial identity | SHA-256 |
| --- | --- |
| Raw final native result | `fe6f62da47f725614508e7d51fefb0a000b83d32c1ea82a7ef095c48d760074e` |
| Host transport, terminal exit `0` | `cbeb02437ead2f122c073b236351d96cfe421fdee763f94ec3113d48ae7b8b72` |
| Native edited output, 60,344 bytes | `c99b33b4f95e478502321e3b1db6649821ac6e72da29ffc48bc73476c434a1c9` |
| Independent typed saved-sibling audit | `d7006261739d2b8e7b30e90528b1ff9724463c2dc8969a8fe91a2f0d4f9b72e5` |

The same frozen serializer closure and unchanged auditor pass twelve scoped stream round trips, two linked re-emissions and all graph/header/lifecycle and edit checks for the second trial. Both persisted material nodes use the resource caption, empty material text and flags `0x80000000`. The plane axes, borders, display state, update stamps and IDs follow the same measured lifecycle as trial one. This does not classify all caches or make saved cache values into generation inputs.

Generated other-axis/reverse native measurements have not been claimed here. The source cohort independently covers those ordinary construction inputs; the constructor uses the shared principal-frame rule rather than per-case saved states. Both held-out native designs remain sealed. A guest-only recipe translator, independent prediction lock, complete writer/tool code lock and controlled blind evaluation remain required before family promotion. No public writer is enabled by these results.
