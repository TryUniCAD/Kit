# SOLIDWORKS archive count primitives

The shared archive implementation now starts in `src/convert/adapters/solidworks/Archive/Counts/`.
These functions generate count bytes from integer cardinalities and documented format rules.
They read no files and require no CAD application or native library.

## Interfaces and limits

`EncodeCount(CountValue, *, IsFramework=False)` returns the canonical little-endian encoding.
`ReadCount(BufferValue, OffsetValue, *, IsFramework=False)` returns the integer and the next byte offset.
The input buffer must be `bytes`.
Invalid types raise `TypeError`.
Negative counts, values outside the selected domain, invalid offsets, and truncated inputs raise `ValueError`.
Booleans are not accepted as integer counts or offsets.

| Selected domain | Count encoding | Largest count |
| --- | --- | --- |
| Vendor `su_CArchive` | u16 below `0xffff`, otherwise `0xffff` followed by u32 | `0xffffffff` |
| Framework MFC | The vendor form below `0xffffffff`, otherwise both markers followed by u64 | `0xffffffffffffffff` |

The domain must follow the native caller.
The [native count record](../../../../re/solidworks/records/MfcCountArchive2026.md) binds the framework grammar to complete 2026 count bodies.
The [count-domain gotcha](../../../Gotchas/Conversion/Solidworks/Archive/FrameworkAndVendorArchiveCountsDiffer.md) records the distinct vendor escape.
The decoder accepts overlong forms, while the encoder chooses canonical width.
The integer does not preserve an overlong representation.
Container allocation limits remain the responsibility of the calling decoder.

## Integration and verification

The research `Core.Load` and `Core.Store` count methods call these production functions directly.
The framework map owner selects `IsFramework=True` through those methods.
Its existing version, archive-mode, row-count, and schema-admission restrictions remain active.

The real archive CLI process checks exercise the shared functions on the discovery and control streams.
Field inventories include both production source hashes, and their process checks verify the exact implementation inventory.
The [promotion receipt](../../../../re/solidworks/measurements/2026/CurveCountAdmissionFeb8.json) binds source `feb8e11db40f0c50f13c9e673cdad87fa9dbc452` to remote run `43816632345`.
Job `133130055908` passed 181 codec/process cases with 158 unrelated fixture-dependent skips.
All 234 strict archive comparisons retain identical bytes and zero tails.
All 234 retained field graphs pass, and their 52 implementation fingerprints match the reviewed sources.
The corpus does not exercise every count-width or malformed-input branch.
Local verification uses source inspection, AST parsing, formatting, diff checks, and remote-artifact analysis only.

This internal layer does not register a SOLIDWORKS writer.
The public adapter remains read-only.
Fresh output construction, held-out vendor acceptance, and complete feature coverage remain unfinished.
