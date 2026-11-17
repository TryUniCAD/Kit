# Legacy Parasolid emission and 2026 cache admission

The SOLIDWORKS 2026 archive builder can omit
`Contents/Config-0-Partition` for independently tested ordinary parts.
SOLIDWORKS rebuilds those bodies from the parametric records. The existing
SDK's default geometry read looks for a supported Parasolid payload, so a
generated cache is a separate geometry and archive qualification.
[2026 stream deletion measurements](../v2026/Deletion2026.md)
[SDK assembly history results](AssemblyInstanceTree2026.md)

| Existing encoder route | Evidence | 2026 generative status |
| --- | --- | --- |
| `EncodeBlankPart` | Wraps two opaque byte constants, `KBlankPartBody` and `KBlankDeltaBody`, with a 2025 Parasolid schema and generated zlib framing. The historical integration test pins a 577-byte wrapper and two exact decoded hashes. The literals entered the repository in `5b511cad0`. | The inner bytes lack field-level construction evidence. Use the measured cache omission for qualified ordinary cases. |
| `EncodeBrepModel` with SOLIDWORKS feature identities | The supplied persistent feature ID is model input. The SolidWorks attribute emitter also writes fixed downstream data, match ID, entity time stamp, density and colour. The literals occur in `WriteSolidAttrs` and its body and face helpers. | The feature identity alone does not account for those values. Qualify these attributes against unrelated native saves and identify their legitimate empty, derived or authored state before using this route. |
| `EncodeBrepModel` without SOLIDWORKS feature identities | `MakeEncConfig` receives an empty feature map. Ordered topology, ownership, surfaces and curves flow through `EncodeBrepBody`. `EncodePartData` derives compressed and uncompressed wrapper lengths. | Measure separately as a generated geometric payload. Its SDK topology, native cache ownership, persistent feature identity and native open and rebuild require explicit checks. |

Trace the current routes in [the Parasolid encoder](../../../src/convert/Geometry/Parasolid.py)
and [the historical wrapper integration](../../../tests/Convert/Formats/ParasolidTests.py).
A successful wrapper or geometry round trip by itself establishes no provenance
for the opaque blank bytes or fixed attribute values. The
[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md#c1-no-donor-data)
require a model input or documented format rule for each emitted value.
