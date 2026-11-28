# MFC complete count-body capture

The optional `--capture-count-bodies` mode of [InspectMfcRuntime.py](../../../../re/tooling/sw2026/InspectMfcRuntime.py) checks the last remaining byte-preservation edge between the two effective exports and their actual count bodies. It captures exact, independently bounded spans from the owned analysis process and requires literal equality with the same spans in the pinned raw runtime. It never invokes either exported pointer or a `CArchive` method.

The option applies only after the existing process, raw runtime, mapped module and export checks. The selected runtime remains System32 `mfc140u.dll`, SHA-256 `88beebf73667ab0d603355f54562aa9cf9316f4d585a40ec93430c6715ffc8d1`. The expected complete body identities are:

| Ordinal | Export thunk RVA | Target body RVA | Complete bytes | Original body SHA-256 |
| --- | --- | --- | ---: | --- |
| `12087` | `0x6bcc70` | `0x557b30` | 288 | `cd381ab524f765a17274de09b371c47ed028f0c3b2b31804eb3871fa71a5c0e4` |
| `14278` | `0x6c5370` | `0x557980` | 424 | `ad9500fd35f8e392d159dbebacd41f377ec1fdbf9f778a25c76c2834af7fda84` |

The 14-byte thunk hashes are `fa55fff220c458e914d00249b5fb46b623778bdde557fe261afeb6883fee0469` and `693ed1a1e4a317c9fed2fa8dc1dee237e7c670b2aae9ebb97c35c5031402e6dd`, respectively. The tool checks the complete hash and the declared x64 relative-jump opcode, decodes the signed displacement and requires the resulting target RVA to equal the selected body. It does not find a body through an unbounded signature scan or follow arbitrary pointers. Microsoft's [Arm64EC ABI documentation](https://learn.microsoft.com/en-us/windows/arm/arm64ec-abi#fast-forward-sequences) explains why an exported x64 fast-forward sequence can lead to an ARM64EC implementation.

The original ARM64 exception directory is RVA `0x9bd000`, size `226360`, with eight-byte entries. Read-count body metadata at RVA `0x9e6570` references xdata `0x92e118`; its version-zero function length is `72*4=288`. Write-count metadata at `0x9e6568` references `0x92e108`; its version-zero length is `106*4=424`. Both full spans include their mode-error tails. They were independently checked against original instruction bytes, not the first unwind fragment or a modified analysis header. The mapped view's separate 180-byte AMD64 exception directory does not delimit these ARM64EC bodies. See Microsoft's [ARM64 unwind format](https://learn.microsoft.com/en-us/cpp/build/arm64-exception-handling?view=msvc-170).

The pinned CHPE code map classifies `[0x337000,0x68e1c8)` as ARM64EC and `[0x68f000,0x6c6190)` as AMD64. These classifications agree with the reached body and thunk instructions. They do not assert that the mapped body bytes were already observed in the earlier export-window capture.

## Usage and output

Append `--capture-count-bodies` to the [existing invocation](SolidworksMfcRuntimeViewInspection.md), using a new committed source identity, fresh owned Python process and unused external output directory. No new path, arbitrary address or capture-length option is added.

The tool verifies each original raw body hash before taking its mapped span. `Ordinal12087CountBody.private.bin` contains exactly 288 bytes; `Ordinal14278CountBody.private.bin` contains exactly 424 bytes. The existing per-read, module/section, fresh-path and total 4 MiB bounds still apply. Both additions together contain 712 bytes. All binary output remains outside checkouts and must never be committed or distributed under the [research artifact policy](../../../Reference/Research/ResearchArtifacts.md).

Each `count_bodies` item records its ordinal, observed thunk hash, decoded target, expected body hash, static extent provenance and private-range record. The latter records the actual mapped hash, observed raw hash and literal `mapped_equals_pinned_raw` result. A mismatching mapped body remains a failed private capture with `full_function_extent_claimed=false`; successful exact equality admits the independently established full span. A checkpoint precedes each body capture. Missing or changed thunks, targets, raw hashes or mapped bytes fail explicitly.

`count_body_capture_requested` records the flag. `count_body_bytes_verified` remains false on incomplete, ambiguous or failed operations and becomes true only after both bodies match and the original raw-file identity and owned-reference cleanup checks pass. The option defaults off. All existing architecture, export, lifetime and capture guards remain active. `instruction_set_proven`, `native_implementation_bound` and `acceptance` retain their always-false scope; successful byte capture is evidence for a separate count-owner review, not a schema promotion.

## Evidence and limits

The earlier `MfcRuntimeView02` run completed under source `067f473f58b6ea804483ff54789c2e78c8e6a0b1`. Inventory SHA-256 `2f85846bb67f141d309031b4a8935a212f7f06528e6dddf52e9cedcc9816a398` records the effective AMD64-facing module, exact export/GetProcAddress matches and successful release. Its two complete captured entry windows equal the pinned raw file. Those windows establish the thunk identities but do not contain the reached bodies. The new option supplied the explicit causal input change for the follow-up probe.

The owner completed `MfcRuntimeView03` with natural transport exit `0` under committed source `925536db6adade2a04c1faf44b5516efd1a79110` and tool SHA-256 `f83885f25f9661fff7fc893cd2e5d63fc9db07c5769e983eb25a6c378c93fb71`. The [sanitized metadata receipt](../../../../re/solidworks/measurements/2026/MfcRuntimeView03.json) binds inventory SHA-256 `6907f9bcf6255b0025193f04a4eb773d8914b1917fe5f169fc0539710fe8df1d`, host SHA-256 `4db5e9f7df0bcbc68d165033d09fb5f5b4d8e48baa72493d2d1f670c063ac03b` and the frozen source manifest. Owned PID `1760` passed process, raw/mapped module, export and release checks. `count_body_bytes_verified=true`: both complete spans match their pinned raw counterparts literally, with the exact hashes listed above. The owner separately rehashed both private captures; the publication worker read metadata and source only. Earlier probe scopes remain unchanged. The natural exit exercised no deadline, and the supervisor observed no progressive record.

Only AST parsing, source/link review and static inspection of retained private images and captures occurred in the implementation worker. No probe, schema, codec, test, guest action, CAD/COM call, external-process access or licensing operation ran there. The reports retain false instruction-set, native-implementation, archive-invocation and native-acceptance flags. The later [separate count owner](SolidworksMfcCountArchiveOwner.md) interprets those grounded bodies before defining `su_CMapStringToInt`; remote source compatibility remains pending, and vendor `Core.count_value` remains unchanged. This byte-equality receipt establishes no CAD/writer acceptance.

The [CAD criteria](../../../Reference/Operations/CadSuccessCriteria.md), [instruction book](../../../../re/Playbook/README.md), [loader chapter](../../../../re/Playbook/LoaderAnalysis.md) and [standard PR skill](../../../../.agents/skills/standard-pr-practice/SKILL.md) remain authoritative:

> The first is success under every criterion on this page.
> The second is the end of the available context.
> Missing grammar is the work. It is not a blocker.
