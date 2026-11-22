# Shared planar mate creation clocks

Task `B04-SW2026-MATES/creation-events`, owner `/root/release_path`, delivery PR #121. The internal planar group constructor accepts independently authored whole-second mate creation events. Its dependencies are the linked Config-0 and Resolved Features graphs, the existing ordered mate and header constructors, and the disclosed A22 bracket on SOLIDWORKS 2026 SP05.2 `34.5.2.0604`. The verification boundary is exact regeneration of that pair using the shared constructor, a separately authored changed event and unchanged omitted-clock behavior. [Native measurement](../measurements/2026/GeneratedRotatedMateNative01.json)

A supplied `GroupMateIn.CreatedAt` uses the existing unsigned Unix-second domain. The mate owns the signed `f2a0` and `f2a4` halves of `(CreatedAt + 11644473600) * 10000000`. Each standalone header adds one `moLogs_c` entry whose `f48` and `f50` identify that same mate and whose `moStamp_c.f18` holds its creation second. The log retains the authored comment and existing attribution rules. An explicit stamp that disagrees with the feature words fails before changing a header or the configuration allocation. Omission uses the existing document creation epoch.

Two fresh guarded workers generated the exact previously measured A22 files from the authored request, using the historical outer stream order. The assembly has 10,351 bytes and the child has 8,643 bytes. The workers consumed no data files during construction and left the public preparation gate closed. The current complete internal assembly includes `Contents/CMgrHdr2` and emits 10,550 bytes. Its distinct file digest still needs its own native evidence. A second, independently authored assembly changed only the distance mate's creation time. Only `Header2`, `Contents/Config-0-ModelHeader` and `Contents/Config-0-MatesList` changed. Both unchanged mate owners, the shared child and every other stream compared exactly. A distance/coincident group without extra clocks reproduced the explicit document-clock version, and five invalid clock inputs refused. [Host evidence](../measurements/2026/SharedMateCreationClocks01.json)

The independently authored native A22 original has nonzero 100 ns remainders in all three feature clocks. Each header stamp equals the whole Unix seconds obtained by dividing its mate FILETIME. Its stored document modification clock precedes both the document creation clock and the mate revisions. Whole-second generated input covers the exact measured cold recipe. Preserving original fractional creation clocks and other saved state, public A22 publication and held-out qualification remain separate exits. [Archive evidence](../measurements/2026/SharedMateCreationClocks01.json) · [Clock ownership](../../../Documentation/Gotchas/Conversion/Solidworks/Assembly/Mates/MateClocksUseSeparatePrecision.md)

```sh
python3.14 -I -B re/tooling/sw2026/rotated_mates/ProveSharedMateClocks.py \
  --disclosed /path/to/NativeMateComboSource04 \
  --output /tmp/SharedMateCreationClocks01.json
```

The supervisor authenticates the disclosed native source, model request, files and bracket separately from the construction workers. The workers receive the neutral request on standard input. The output receipt contains typed measurements and digests. [Verifier](../../tooling/sw2026/rotated_mates/ProveSharedMateClocks.py)
