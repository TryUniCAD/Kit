# SOLIDWORKS 2026 standalone downstream archive body

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` uses the shared Kit archive to encode and read the direct `moDownstreamIdData_c` body. This research codec covers ordinary version 19000 in a standalone context. The root owns codec integration and native acceptance in PR #121.

The direct call uses the known logical map base of one. The root has neither a pointer tag nor a class or object registration. The existing archive callbacks register every nested class and object in the same namespace. All 18 counted sections use ordered rows and signed 32-bit counts. Each count derives from the supplied rows. The five identity tables consume a pointer only for a nonzero key, and the admitted `uniqueIdInfo_c` body ends with its high and low packed words. [Native field grammar](DownstreamIdArchiveGrammar2026.md) · [Standalone map source](DownstreamStandaloneMaps2026.md)

The prefix retains the exact u32 wire word of `su_CTime`. The UUID uses the shared `CString` representation, including the source encoding distinction. The isolated layout supplies the direct body and the unique-info object only. Each other nonnull reference requires a source-proven concrete layout and applicable class context before it can be used for a cache.

## Shared component body suffix

The exact-build `sldmodu.dll` Serialize table slot at `+0x28` binds `moCompSolidBody_c` to a five-byte tail jump into `moCompAtomBody_c`. The surface class calls that same serializer and then sets bit `0x4` of the inherited flags field `+0x68` on load. This post-read operation consumes zero archive bytes. Both classes retain their distinct runtime class tags. [Surface-body flag gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/SurfaceBodySetsFlagAfterLoad.md)

| Owner | Primary table | Complete Serialize range |
| --- | --- | --- |
| `moCompAtomBody_c` | `0x4cd91fe0` | `[0x4bba4390,0x4bba46b7)` |
| `moCompSolidBody_c` | `0x4ce93810` | `[0x4bba6b10,0x4bba6b15)` |
| `moCompSurfaceBody_c` | `0x4ce93338` | `[0x4bba8310,0x4bba8341)` |

At ordinary version 19000, the shared serializer calls `moCompRef_c::Serialize` and writes the following suffix in order. The existing Kit solid body layout has the same field order. The direct downstream codec needs the reached component and face-reference layouts for the same context before admitting these objects. [Component base and edge field order](DownstreamComponentWire2026.md)

| Runtime owner | Wire field |
| --- | --- |
| `+0xf0` | Typed `moFaceRef_c` archive pointer |
| `+0x120`, `+0x118` | Signed i32 count and that many i32 values from the backing array |
| `+0x108` | i32 |
| `+0x104` | i32 body atom ID |
| `+0x100` | i32 face node ID |

On ordinary store, the serializer first clears `+0x100`. With condition `0x80` clear and a valid runtime face at `+0xf8`, it takes the node ID from that face. If the face also has a valid body, it takes the atom ID from that body. The native calls source these values from the kernel graph. The production read/write and their ID lifecycle require a saved control for the reached context. The [process and native source receipt](../measurements/2026/DownstreamStandaloneBodyCodec01.json) records the exact module and complete dependency hashes.

## Replay

```sh
PYTHONPATH=src:.:re/tooling/sw2026 python -B -m downstream.CheckBody
```

Two fresh SDK processes reproduce the 113-byte empty shape, 355-byte populated ANSI shape and 394-byte populated wide shape. They check independent scalar and text framing and preserve class slot 1, object slot 2 and five shared references to that object. Each repeats all three inputs under an audit hook that rejects runtime file opens, subprocess launches and socket connections. Eight invalid cases refuse.

The populated cases exercise every counted section with synthetic rows. The component pointer rows use nulls and the shared identity object tests raw archive aliasing. Native cache reconstruction can discard nulls, normalize collections, clone identity values or destroy temporary read objects. The codec evidence applies to wire framing. A byte-exact replay of a disclosed saved stream, an actual standalone save invocation, a complete generative cache and linked drawing acceptance remain open.

The linked profile now exercises nonnull component, entity and surface-ID objects in modeled part and drawing contexts. [Linked reference codec](DownstreamLinkedReferenceCodec2026.md)
