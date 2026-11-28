# Typed archive replay for the assigned-density diagnostic

The version-19000 `Config-0` and linked `Config-0-ResolvedFeatures` of the tracked
`named-material/AssignedDensityProbe.SLDPRT` re-emit byte for byte with zero opaque
operations in a scoped research process. Four fresh workers repeat the same checks on
the assigned diagnostic and the unassigned L1 contrast. [Exact receipt](../measurements/2026/AssignedMaterialStreamsReplay01.json)

Task `B04-SW2026-NAMED-MATERIAL`, owner `/root/release_path`, delivery PR #121. This
closes the typed binary replay boundary for these two streams and the documented
fixture. It depends on the established model-member and Windows GUID rules, the
strict assigned-material reader, and the shared resolved codec. Model-based
construction, appearance and material tree transfer retain their own gates.

| Assigned stream | Bytes | Recomputed map counter | SHA-256 |
| --- | ---: | ---: | --- |
| `Contents/Config-0` | 26,294 | 110 | `5da5363400dd14c132c145167760cb6ee9933feb6f4d0bd73a5b1cceb0a0f26b` |
| `Contents/Config-0-ResolvedFeatures` | 15,069 | 300 | `cef4349eb07028839313447a8a0670165bcad6a1f36c436126f07d194485e1b5` |

## Nine legacy counts, three physical fields

The legacy census uses three fixed-width raw operators in each direction for
`Config-0`. Its linked ResolvedFeatures reader also counts the three reads
needed for the predecessor configuration map. The legacy ResolvedFeatures
body itself adds zero raw operations.

- `moModel_c.FUN_4c22ec80.f784` and `f7a4` are each 16 zero bytes in this profile.
  The proof reads each member as scalars and requires every scalar to equal
  the documented constructor initializer. [Model initializer](ModelConstruction2026.md)
- `moSketchBlockMgr_c.f380` owns a Windows-order UUID4. The proof reads the
  little-endian 32-bit and 16-bit components and eight byte components, builds
  a typed UUID and checks the actual empty block map and owner backlink. The native
  constructor calls `CoCreateGuid`; the ordinary serializer reads and writes
  precisely this member at `0x4c90b246` and `0x4c90b25b`. The separate
  diagnostic and unassigned L1 files share this retained UUID, so the contrast
  provides no held-out or independent GUID-allocation credit. [Block manager](CommonPartOwners2026.md#sketch-block-manager-and-owned-block-map) · [Creation rule](DrawingEmptyManagers2026.md)

The proof reuses the SDK's guarded version-19000 material context, physical
header alias chain and generic typed field executor. Only the three declarations
above change inside the research context. The material route independently
confirms material ID 258 at 2700 kg/m³, linked to body atom 101 and feature 34.
The unassigned file refuses the named assignment. The emitted configuration map
has the same actual entries as its decoded graph and supplies the seed for the
unmodified SDK ResolvedFeatures reader and writer. Their three counted display
records per direction are fully typed binary64 arrays. Both workers reject
unconsumed data, provisional or missing schemas and any opaque operation.

Run from the pinned SDK closure. The tool reads two hash-pinned Git objects
outside the guarded workers. Codec execution makes zero file or process accesses.

```sh
python3.14 -I -B re/tooling/sw2026/materials/ReplayAssignedStreams.py
```

This evidence covers typed re-emission of disclosed source archives. It establishes
zero opaque operations in this proof and leaves the general census's legacy
counts reproducible. It supplies no new native acceptance or product output.
