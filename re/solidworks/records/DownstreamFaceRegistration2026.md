# Fresh downstream face registration, SOLIDWORKS 2026

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` is delivered in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). Root owns the generated projection and native qualification. The source pins cover SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` and Parasolid 37.01.250.

## Row identity and cache clock

Fresh downstream population at `0x4b5263c0` calls `GetSystemTimeAsFileTime` at `0x4b526478` with data `+0xbd0` as the destination. It records the cache construction time once before building the face and edge rows. The generator takes an explicit cache construction event in this domain. The ModelHeader update second and the partition's downstream allocation FILETIME have their own producers.

Face registration calls `0x4b5293d0` at `0x4b52b44b` with type `0x138c`. Edge registration reaches it at `0x4b52af07` with type `0x138a`. Both pass a null optional clock override, so the builder copies data `+0xbd0` into each actual `uniqueIdInfo_c` record. The types select the separate `f340` and `f380` tables.

| Wire field | Producer |
| --- | --- |
| Table key | Actual allocated downstream ID. |
| `f08` | The checked zero-based ordinal of the wrapper in the corresponding face or edge vector. |
| `f0c` | The actual body atom copied into wrapper `f18`. |
| `f10` | The actual face or edge node identifier. |
| Packed high then low | The two words of the same cache construction FILETIME. |

The node identifier call reaches `gcEnt_w::getNodeId` at `0x439d74d0` and the Parasolid wrapper `0x33017fc0`. Its kernel import `PK_ENTITY_ask_identifier` reaches `0x180245880`. The selected leaf `0x180a8b8a0` reads the first dword of the valid ordinary face or edge node. The emitted active partition carries that value in its typed `node_id` field. [Original source windows](DownstreamFaceRegistration2026.json) · [Partition fields](PopulatedPrismPartition2026.md)

## Six-face order and readback

The fresh `f340` initializer creates eight buckets with mask seven and maximum load factor one. Insertion uses FNV-1a over the four key bytes for bucket placement. Face keys one through six select buckets `4,7,6,1,0,3` in allocation order. Every insertion sees an empty bucket and stays within the original load limit. That branch appends before the shared list sentinel. The serializer walks the list forward, so the six entries serialize in allocation order.

The projection takes the six retained typed face rows from the existing no-collision replay and checks them against the actual partition chain and body atom. It adds their `f340` table to that cache witness. Edge registration field ownership is mapped in source. Edge wrappers, edge-map growth and complete cache qualification remain separate steps. [Generated face validator](DownstreamPrismFaceStore2026.md)

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  python -B -m downstream.CheckFaceRegistration 1
```

Variants `1` and `2` each run in two fresh processes, preserving the generated part streams and reproducing their cache bodies exactly after readback. Each compares six lookup rows with the actual emitted partition. Changing the supplied cache clock by one tick changes the timestamp while preserving the ordinal, body atom and node ID. Guards record zero external operations after registry and Python initialization. [Process receipt](../measurements/2026/DownstreamFaceRegistration01.json)

Replay the source proof using `VerifyFaceRegistrationSources.py --bin-directory <original-model-directory> --kernel <original-kernel-path> --record <this-json-record> --output <fresh-path>`. It verifies the complete pinned functions, instruction windows and import identities in the original modules. [Source verifier](../../tooling/sw2026/downstream/VerifyFaceRegistrationSources.py) · [Source receipt](../measurements/2026/DownstreamFaceRegistrationSource01.json)
