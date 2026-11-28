# Linked downstream reference codec and construction inputs

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` is delivered in PR #121. Root owns the codec, generated topology projection and native acceptance. The version-19000 research profile uses Kit's shared field executor and preserves the fresh standalone map across the complete modeled graph. [Standalone archive map](DownstreamStandaloneMaps2026.md) · [Direct archive body](DownstreamStandaloneBodyCodec2026.md)

## Recursive body replay

The body profile combines six component classes, face, edge and vertex reference classes, and two reached surface-ID representation classes. The same map stores all of them. It uses the existing component base, atom, direct entity reference, face and inline entity ID fields. The new research layouts supply composite-edge fields, the edge alias, the vertex point, inline face matches and the embedded reference map and vector. [Component source](DownstreamComponentWire2026.md) · [Entity-reference source](DownstreamEntityReferenceWire2026.md)

The two reference layouts that differ in a drawing context retain their four-word tails. The part profile consumes the known part fields. A drawing-context replay of the same shape adds 32 bytes at the two verified owners. It preserves the stored drawing identity fields as input values. Actual drawing identity assignment, application save dispatch and native rehydration require their own evidence.

| Guarded input | Bytes | Concrete classes | Occupied archive slots |
| --- | ---: | ---: | ---: |
| Modeled part reference graph | 1,491 | 11 | 22 |
| Modeled drawing-context graph | 1,523 | 11 | 22 |

Two fresh SDK processes reproduce both byte streams. Repeated links preserve their archive identities across the outer tables, shared vertex reference, face references and inline ID representations. Independent primitive checks cover both match rows, three map pairs, three vector words, the optional point and both drawing tails. Raw replay retains duplicate keys and vector zero values before native normalization. Nine invalid count, type and context cases refuse. [Normalization gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/EntityReferenceRowsNormalizeOnLoad.md)

The profile admits version 19000 with ordinary non-DB framing and helper `+0x48` unset. It accepts two concrete ID representations. The optional component owner, extended reference and feature-reference pointer remain open. A disclosed standalone cache is still needed to qualify actual reached classes and helper state for native bytes.

## Generated solid ownership

The input projection joins the actual generated edge to the two fins owned by its adjacent face loops. The observed body link order supplies the shared downstream allocation. The incidence walk checks each fin ring, its loop and face owner, reciprocal fin pairing and complete coverage. It retains both incidences when they reach one face. For the ordinary two-fin profile, a line or circle curve owned by the edge and opposite fin senses identify the positive fin as the native oriented coedge. Its face supplies key 0. The partner face supplies key 1. Both values come from the actual face allocation. [Fresh assignment source](DownstreamFreshReferenceAssignments2026.md)

Two independently generated prisms and two cylinders reproduce their partition bytes. A separate read of the emitted fin, loop, face and edge references and downstream attributes confirms 56 incidences and 56 role assignments. Reversing the first-fin link preserves the role rows for all 28 edges. Sixteen malformed topology trials refuse. Completing the reference graph still requires the conditional start/end roles, actual feature ID representations and component owner objects.

## Constructor fields

| Word | Classification and rule |
| --- | --- |
| `f08` | Starts at one. The fresh allocator computes the value after the face and edge traversals. |
| `f0c` | Current file format version, 19000 for this build profile. |
| `f10` | Exact original build metadata, 2026306 on the tagged-date cache-miss path. |
| `f14,f18` | Zero on construction. Populated meaning remains open. |
| `f1c,f20` | 101 on construction. Later update semantics remain open. |
| `f28` | Runtime calendar sentinel for local midnight on 1990-01-01. The wire stores the resulting Unix-seconds word. |

The prefix constructor takes the target UTC offset at the sentinel instant in whole minutes. It derives the time word without the current clock or a timezone database read. Three offsets agree with an independent packed prefix in each geometry process. The result describes the constructor state. Populated timestamps, reference modes, native save and held-out acceptance remain open. [Constructor source](DownstreamConstructorEnable2026.md) · [Build code source](DownstreamDateAndEnable2026.md)

## Replay

```sh
PYTHONPATH=src:.:re/tooling/sw2026 python -B -m downstream.CheckReferences
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  python -B -m downstream.CheckCacheInputs prism 1
```

Use `prism` or `cylinder` and variant `1` or `2` for the geometry replay. The guarded phases recorded zero file opens, subprocess launches or socket connections. All results are host process evidence with zero vendor runs or saved model cache reads. [Process receipt](../measurements/2026/DownstreamLinkedReferenceCodec01.json)
