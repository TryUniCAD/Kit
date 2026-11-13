# Fusion protein assets carry account data in heap residue

## Expectation

A saved Fusion design holds design data, material data and a few document identifiers. A privacy scan of the outer `.f3d` members should find any account data in the file.

## Actual behavior

Fusion stores material and appearance assets as `ProteinAsset.*.protein` members. Each of those members is itself a deflated ZIP archive. Its `AssetData/InstanceProperties.bin` and `AssetData/DefinitionIteratorProperties.bin` members contain byte ranges that Fusion fills from uninitialized heap memory.

That residue holds fragments of Fusion's telemetry and session JSON from the saving machine. The fragments included hub ids, hashed hub ids, space collection ids, user ids, file ids, session ids, owner display names, cloud lineage URNs and home directory paths. Many fragments start in the middle of a key or a value. Others repeat part of a value with no key at all. A scan for complete `"key":"value"` pairs misses them.

Kit's readers do not decode the residue. `ReadDocument` models did not change when the residue was replaced, and `ReadFusionDoc` documents changed only in the whole-archive digest and passthrough payload.

The census of the 366 Fusion archives that the native I/O work added found residue in 77 of them. Every affected byte was inside a nested protein ZIP.

| Nested member | Members with residue |
| --- | --- |
| `AssetData/InstanceProperties.bin` | 63 |
| `AssetData/DefinitionIteratorProperties.bin` | 42 |

No outer member held account data. A scan that reads only outer members, or that searches compressed bytes, finds none of it.

## Workaround

Recurse into every nested ZIP and scan the decompressed member bytes. Treat a value after an account key, a key tail or an owner marker as private. Then search the same run for fragments of each learned value, because truncated copies appear without keys.

Run [`ScrubSaved.py`](../../../../../re/Fusion/LocalOracle/ScrubSaved.py) on Fusion-saved archives before committing them. It replaces account values, display names, home directory names and cloud ids with same-length placeholders. It recompresses only the changed members and keeps member order, names, compression methods, timestamps, attributes, extra fields and comments. Record the saved and committed digests in the scrub ledger, and update every report that cites the saved digest or size.

## Evidence

- [Scrub ledger](../../../../../re/Fusion/LocalOracle/ScrubLedger.json)
- [Scrubber](../../../../../re/Fusion/LocalOracle/ScrubSaved.py)
- [Fixture scrub change entry](../../../../Changes/Fusion/Privacy/FusionFixtureScrub.md)
