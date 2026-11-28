# Exception-directory size bounds AMD64 unwind records

## Expectation

Every 12-byte row in the PE `.pdata` section's raw allocation is an AMD64 runtime-function entry. Reading that complete allocation gives reliable function boundaries.

## Actual behavior

PE raw section size includes alignment padding after the exception data directory. Treating the padding as more runtime-function entries invents rows. Unwind traversal can then follow zero or unmapped RVAs, or associate invalid extents with a serializer. That is a static inspector failure, not evidence of a CAD loader or format crash.

Direct reads of the pinned 2026 images give:

| Module | Exception directory size | Valid AMD64 entries | `.pdata` raw size | Excess raw bytes |
| --- | --- | --- | --- | --- |
| `sldmodu.dll` | 988296 | 82358 | 988672 | 376 |
| `sldmfcu.dll` | 222504 | 18542 | 222720 | 216 |
| `swccu.dll` | 11748 | 979 | 11776 | 28 |

Their exact SHA-256 identities and complete serializer fingerprints are in the [common-owner record](../../../../../re/solidworks/records/CommonPartOwners2026.md). Reading to raw section size would additionally attempt incomplete rows in the model and common-support images because their raw sizes are not multiples of 12.

An unwind-info RVA is also not a unique function identity: distinct functions can share that unwind descriptor. The environment-folder and exploded-view serializers both refer to unwind info `0x4d385bbc`, but have different runtime-function rows and function extents. Following only a single row can also truncate a function whose unwind chain names further fragments.

## Workaround

Read exception directory index 3 from the PE optional header. Translate that directory's RVA through the section map and parse exactly its declared byte size. Validate the machine and directory bounds first; the 12-byte `RUNTIME_FUNCTION` layout here is AMD64-specific and is not an ARM64 or ARM64X unwind parser.

For each selected entry, follow `UNW_FLAG_CHAININFO` to its complete parent runtime-function tuple, aligning the unwind-code area to four bytes before reading that tuple. Group by the resulting full tuple, not by unwind RVA alone. Record every reached fragment and the full native span used for a fingerprint. Validate bounds against executable sections. A leaf without a runtime-function row needs an independently verified instruction boundary; absence of an exception row does not prove absence of a function.

The common-owner investigation used the authoritative directory size before computing its serializer fingerprints. Only static PE and instruction inspection occurred. No proprietary image or decompiled listing belongs in the repository, and these function-boundary facts establish no native CAD acceptance.
