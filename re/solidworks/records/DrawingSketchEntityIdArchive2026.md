# Drawing sketch entity surface IDs in SOLIDWORKS 2026

The two disclosed originals still reject at the first concrete surface-ID dependency in the preceding reader. This separate tranche admits two exact concrete schemas whose complete raw layouts already exist in the shared SDK. It does not change a field rule, construct an entity ID, or qualify drawing semantics or output.

Task: PR121 ordinary drawing edge-ID closure. Owner: `flag_ownership`; delivery PR: #121. Dependency: the exact [edge reader tranche](DrawingEdgeReferenceArchive2026.md). Exit: independent source/field proof, a fixed one-file concrete-schema extension, a real prior-profile regression, and retained exact original parser outcomes or next boundaries. Native and held-out writer acceptance remain separate.

## Concrete identity

All native evidence is from `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, version `34.5.2.0604`. The [JSON proof](DrawingSketchEntityIdArchive2026.json) binds exact original bytes, full exception-directory fragment closures, concrete primary tables, runtime descriptors, and the embedded member receiver.

| Owner | Actual primary table | Schema / size | Actual serializer |
| --- | --- | --- | --- |
| `moFromSktEntSurfIdRep_c` | `0x4cf6ab10` | `0x80000001` / 64 | `0x4bbaa6a0` |
| `moFR_c` | `0x4cf5ade0` | `0x80000001` / 40 | `0x4bb34e90` |

The surface-ID RTTI path is `moFromSktEntSurfIdRep_c → moSingleSurfIdRep_c → moSurfaceIdRep_c → moEntityIdRep_c → gcEntityIdRep_c → su_CObject → CObject`. The factory at `0x4bb95d00` installs the actual primary table at `0x4bb95d6a–0x4bb95d71`. This identifies the concrete receiver independently of a class-name search.

The historical SerializeMap points this class to `0x4bc267a0`. That address lies inside the different full function `[0x4bc260a0,0x4bc268bc)`; it is not the actual primary-table serializer. The same map gives `moFR_c` as `0x4bbb1a00`, while its primary table directly binds `0x4bb34e90`. The global map is untouched. These class labels must not override actual runtime descriptors and primary dispatch. The existing [concrete-dispatch gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/Qualification/SharedSerializerSymbolsNeedConcreteBinding.md) applies.

## Field ownership and wire order

For ordinary version 19000 the complete surface-ID body is an embedded FR keeper at `this+0x10`, followed by signed `f38:i32`. No class tag is added for the embedded keeper.

1. The 78-byte wrapper `[0x4bbaa6a0,0x4bbaa6ee)`, SHA-256 `e957dd0dbbb720aeb20df845f106cfee9c335b47eec6f70276111fb780f7fb30`, calls the shared `0x4bba8790` base and then reads or stores `this+0x38` using the signed-long primitive
2. The complete base `[0x4bba8790,0x4bba8bb2)`, SHA-256 `d0f445160a0fdf2f602735dbe3f76421054a8d4e7ea0e674f805f6e6f51a25cc`, selects the modern member-virtual path at versions at least `0x21b`
3. The factory constructs the member at `this+0x10` using `0x4bb5d2a0`. That complete 127-byte constructor installs `0x4cf60db8`; its virtual slot zero is `0x4bba8de0`, the complete 2,130-byte FR-keeper serializer
4. That keeper reads one raw object reference `f08`, then one typed `moFR_c` object reference `f10`. The vendor operators at `0x4bb34810` and `0x4bb348d0` bind descriptor `0x4dadabd0` for the latter
5. The concrete `moFR_c` body reads `f08:moExtObject_c` then embedded `moFRData_c`. The latter is current-version `f00:i32` plus raw `f08:time32/u32`

The [existing reference layouts](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/ReferenceFields.py), [feature layouts](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/FeatureFields.py), and [component layouts](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/ComponentFields.py) already encode this sequence. This tranche only adds two concrete schema-one entries to the drawing profile. Every decoded field remains an input wire value. There are no generated defaults, offset programs, source-specific branches, or fresh constructor values.

The native FR keeper can suppress/remap references during save and share, delete, or remap runtime references after load. Those operations do not add current-version wire fields. The raw SDK codec preserves the original typed values and aliases and does not imitate native runtime fixups. A complete raw replay is not a guarantee that arbitrary raw states are valid fresh constructor or native save states.

## Context limits

The drawing layout entry still admits only archive version 19000 and its ordinary non-database context. The edge owner already rejects nonzero helper+48 and special FRData modes. Conditions zero and the ordinary temporary view bit `0x40` use the same selected field sequence here. Retention registries used under `0x200000` on load and `0x8000000` on store add no wire words and remain outside the ordinary profile.

The legacy pre-`0x21b` representation, pre-`0x3ad` retention, old FR name strings and extra legacy words are excluded by the current version guard. The public part/assembly readers, shared field programs, old drawing writer, its failed original semantic verdict, and all constructors remain unchanged. Any reached external-reference concrete class must still pass its own current drawing admission.

## Verification and remaining work

The single SDK file passes AST, Black, Ruff, strict Mypy, strict Pyright, steering, and the recorded-payload static check. The worker ran no local product probe, test suite, native application, or VM operation. The exact frozen closure has 4,350 files. Root independently passed all 43 prior-profile workers on the exact frozen source with source immutability retained. The exact two original probes advance to `moEndFaceSurfIdRep_c` schema one, at cursor 31,920 and 31,916 with next map counter 226. Both edge bodies and full streams remain incomplete. The [receipt](../measurements/2026/DrawingSketchEntityIdReader01.json) binds both real results.

The preceding edge snapshot's real original failures remain retained: `moFromSktEntSurfIdRep_c` schema one, cursors 31,636 and 31,632. The new end-face failures are retained alongside them. No complete source stream, edge body, populated downstream helper, public semantic admission, native acceptance, or held-out writer acceptance is credited.

Confidence: concrete native identity and selected raw grammar are confirmed static facts. Entity meaning beyond the structural field ownership, runtime fixup semantics, generative endpoint construction, complete source closure, and native application acceptance remain partial or unmeasured.

The governing stopping conditions are unchanged: “The first is success under every criterion on this page.” and “The second is the end of the available context.” Missing grammar remains work.
