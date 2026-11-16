# Framework count owner for the string-to-int map

The 2026 research serializer adds a separate framework count operation and a bounded `su_CMapStringToInt` owner in [MfcMaps.py](../../../../re/tooling/sw2026/serial/defs/MfcMaps.py). It preserves the existing `n/items/k/v` fields, CString and integer row operations, and repetition safeguards. The vendor archive count grammar remains unchanged.

The new count operation reads u16, escapes `0xffff` to u32, then escapes `0xffffffff` to u64. Store uses u16 below `0xffff`, marker plus u32 from `0xffff` through `0xfffffffe`, and both markers plus u64 from `0xffffffff` through the unsigned 64-bit maximum. Unsupported count values fail explicitly. No count, row or model value has a default. Native store uses canonical width; overlong count inputs can therefore normalize on store, so arbitrary noncanonical byte identity is not claimed.

The owner requires the existing ordinary Core load/store implementations and effective document version `19000`. Other implementations and explicit versions fail before the owner payload is processed. The existing unspecified/zero-version convention still selects current version. Native DB-mode behavior is excluded: Core exposes no native archive-mode word or DB grammar, and its `conditions` metadata is not that mode word. The existing decoder repetition limit remains 10000000 rows; native u64 count capacity does not raise it.

The normal sorted definitions loader discovers the module. It replaces the provisional declaration through existing registry behavior, without a new command or flag. Use the [research serializer guide](../../../../re/tooling/sw2026/serial/README.md) and existing strict usage reporting in the parent-owned verification process. The [native field record](../../../../re/solidworks/records/MfcCountArchive2026.md) binds the direct map call, both count imports, complete native body extents, mode gates and all image/function hashes. The [count-family gotcha](../../../Gotchas/Conversion/Solidworks/Archive/FrameworkAndVendorArchiveCountsDiffer.md) explains why the vendor core must not share the new escape.

## Evidence and limits

The pinned effective MFC exports lead through exact x64 fast-forward thunks to complete ARM64EC count bodies. `MfcRuntimeView03`, under committed source `925536db6adade2a04c1faf44b5516efd1a79110`, captured those complete 288/424-byte bodies. Both are literally equal to the independently inspected original spans. Inventory SHA-256 is `6907f9bcf6255b0025193f04a4eb773d8914b1917fe5f169fc0539710fe8df1d`; host receipt SHA-256 is `4db5e9f7df0bcbc68d165033d09fb5f5b4d8e48baa72493d2d1f670c063ac03b`. The [capture tool](SolidworksMfcCountBodyCapture.md) released its own runtime reference and invoked no count, CAD, COM, service or licensing method. Its acceptance flags remain false.

The [source-admission receipt](../../../../re/solidworks/measurements/2026/CurveDiscoveryAdmissionCf26.json) binds source `cf26e9f113b17f4503b66f7268941d256f6706be`, workflow run `43806765968`, job `133099223531` and artifact `14198658366`.
All 234 discovery/control archive comparisons pass strict admission with byte identity, zero tails and no reached provisional or missing schemas.
All 234 retained field graphs pass their process checks.
The job records 171 policy checks and 181 codec/process cases passing, with 158 unrelated fixture skips.

The earlier `b291c4da` job remains a historical two-failure assertion-contract result.
Its successful source reports and all 50 serializer implementation files equal the current ones in complete bytes.
The repair reconstructs aggregate usage summaries from actual phases and preserves their completion checks.
No schema, codec, product or test executed locally.

The source corpus does not exercise every native count-domain or version branch.
Matching bytes do not establish fresh writer, held-out model, rebuild, edit or geometry acceptance.
No production adapter, native dependency, runtime file read, saved field value, captured row or donor fallback is added.
The [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md) still govern every output claim:

> The first is success under every criterion on this page.
> The second is the end of the available context.
> Missing grammar is the work. It is not a blocker.
