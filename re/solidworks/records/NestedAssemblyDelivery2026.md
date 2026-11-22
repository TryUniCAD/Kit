# Rigid nested assembly delivery

The PR #121 takeover owns `B04-SW2026-RIGID-NESTED` on `codex/solidworks-public-nested-assembly`, based on the first ordinary part writer at `515d58a9e8e7dac8d9836cf21b2a054a1897143c` and its updated foundation `1a9cc8446e83e2b947d680f467d4470d6e42079f`. The assembly constructor rules come from `0f2444beb33c558bf78e7a48cb87047d04d6709b` and the earlier public byte-parity path at `96fe5d97f67efc03bcf394f9b3e3caaa5e9469fb`. The scoped branch shares the ordinary part constructor, archive writers, Definition, history and publication transaction. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) [Writer model](../../Playbook/WriterModel.md)

The writer allocates a complete target for each real definition in dependency order. Direct placement order determines the parent reference directory and per-occurrence configuration rows. Repeated definitions retain one generated target, while recursively expanded occurrences contribute to header activity. Each selected configuration, owner, file kind, creation stamp and placement derives from the actual model and generated child. The assembly writes two headers, Config-0, ResolvedFeatures, CMgr, CMgrHdr2, Definition, History, Biography, KeyWords, the component tree and an empty MatesList. The empty list writes the live inherited ResolvedFeatures counter and the canonical empty count.

The assembly Config and Resolved contexts extend the accepted part rules only for assembly emission. In CMgr, `moConfigObject_c.fd0` emits its own list with condition 512 set for that list and cleared afterward. A conditional test of preexisting flag 512 omitted one two-byte count per component row and changed only CMgr. The current constructor uses the existing context setter, list and clearer. The two driving sketch dimensions use the actual point-pair runtime class and handle grammar in the dimensioned leaf context.

The [original disclosed public receipt](../measurements/2026/SdkPublicNestedWriting01.json), SHA-256 `2cb15c011cad7cd489a3657c65765192cfb9bd7a08d2c46128375d892f1df41a`, was reproduced at `c148c335e1b8f892933baa3227841e32b62e6a4e`. Thirteen fresh processes compared both public routes to the four pinned native-tested bundles, including two repeated and two three-driver cohorts. All fourteen complete file hashes matched on each route. Five refusals left output intact. A separate guarded preparation comparison matched all 156 stream hashes to the pinned aggregate constructor.

The [candidate publication receipt](../measurements/2026/SdkNestedCandidateParity01.json), SHA-256 `5a403625fc74702531215fd41c88ebb9ecdbf08d70212da9e06865944df5e6f8`, used Git source tree `58bf9509a2d141c77fb4f4bb7f4009e1f70d72b8` and the [guarded probe](../../tooling/sw2026/nested_delivery/ProveNestedDelivery.py) with SHA-256 `c59c15a21155472ce5f4ab89da749c259e91914d451053d883e8d23bcfda60d4`. Seventeen fresh data-only processes reproduced all fourteen exact files on both public routes, with all eight native transfers and zero runtime input-file reads. Both acceptance flags were false on every write. Each strict route discarded a complete four-file staged bundle, reported both missing measurements via `ApplicationUsabilityError`, and made zero final publication attempts. Omitting the explicit native transfer requirement refused the candidate before any staged file write. The five earlier refusals also preserved the destination. This run started zero SOLIDWORKS processes and accessed zero protected inputs.

A separate standalone `Skew` request with SHA-256 `884af6d4e091475a83322eeb795755c0bb28fe9dbf65b5817088f1a4b71cd8e9` produced identical 8,092-byte files from the original part base and the initial scoped assembly revision. The generated container SHA-256 was `c4178331d63a90913d670e45d67612a7048b1bb58e1fa9fd8cee8444b802edb3`, with all six native transfers and zero input file reads on both calls.

```sh
python3.14 -I -B re/tooling/sw2026/nested_delivery/ProveNestedDelivery.py \
  --workspace /disclosed/oracle/parent --output /fresh/external/Result.json
```

The earlier [native locked receipt](../measurements/2026/SdkSealedNeutralNestedNative01.json), SHA-256 `48de61872b805bcb2acf3cec9f8d6a491629e3b1a9560f452985c2583b0658de`, records eight native processes and healthy controls for the two independently locked hierarchies. The [sealed public parity receipt](../measurements/2026/SdkSealedPublicNestedParity03.json), SHA-256 `ef7105a0b13984cbdfe99ff3a419637c831f2cd89996d36924380dd526599bb2`, binds both public routes and their eleven exact files to those native-tested Windows bundles. The scoped extraction rechecked the disclosed inputs. It has zero additional native or sealed executions.

Publication, configured review and CI remain separate exits. Nested mates, whole-source native re-export and the original FCStd assembly roster remain open. [Guide](../../../Documentation/Reference/Adapters/SolidworksAssemblyWriting.md)

The native index identifies definitions by their file rows. Their shared root display name does not identify a definition. The disclosed repeated three-driver assembly has four distinct native definitions and seven expanded paths. The public read with `include_brep=False` retains four definitions and five direct occurrence records. The default strict B-rep reader for the three-driver cold leaves refused the missing saved Parasolid payload. The writer proof compares the complete native files and the native component index directly. [Cold reader coverage](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/NestedColdReaderCoverage.md)

## Exact measured publication

The assembly preflight follows the standalone part SDK envelope from `7b0744c97cd54fb21f0c82f175ec7ffb37ae319f`. Its receipt represents one rigid nested bundle. The offline reader separately checks the pinned packet, fixture, two independent model-build records, prediction, native terminal report and four phase records. It derives the member names, selected configurations and ordered child identities from the actual resolved scene and closes that inventory on the cold, rebuilt, edited and reopened states. The source build performs two model-only generations. Each measured phase reopens the original generated or synchronized edited artifacts under the exact SP05.2 identity. [Offline evidence reader](../../tooling/sw2026/nested_delivery/ReadNestedEvidence.py)

The measured assembly configuration is `Default`. The literal part configuration `modeled default` was itself measured by `GetConfigurationNames` and `ActiveConfiguration.Name`. The independent component traversal checks `ReferencedConfiguration` and the resolved physical file for each occurrence. Plain leaves retain measured boss depth. Dimensioned leaves also expose both expected sketch lengths. These disclosed lifecycle measurements edited one leaf boss depth, checked its effect on the root, then saved and reopened all owned definitions. Separate native edits to both sketch lengths were outside this lifecycle. The actual leaves, subassemblies and root share creation epoch `1794700075` at `moFileDefinition_c.f60`. [Creation epoch gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/NestedBundleCreationEpoch.md)

The runtime reads a caller-authenticated, unsigned measurement in memory. Before the first staged file open it verifies the timed, distinct native bracket, requires the one measured namespace and root, and hashes all computed files. Each ordered row must match its ID, basename, selected configuration, ordered direct child IDs, length and digest. The ordinary transfer and transaction checks still protect the destination. The matched proof describes use in the measured hierarchy, including the linked leaf documents in that context.

The [measured SDK receipt](../measurements/2026/SdkMeasuredNestedPublication01.json), SHA-256 `66479552b24b577a3c0bff047efd39482255a1ed9f0af213d2b4dc8ab4bc8437`, records 44 guarded processes on Git source tree `4212574a652a4b275c53122bc930e5d9da151469`. Both SDK routes reproduce all 14 complete files across the four disclosed bundles and make all eight native transfers with zero runtime input reads. Fifteen evidence and changed-model contrasts each refuse on both routes before staging any file. The five prior destination and model refusals also have zero staged writes. A controlled first-companion publication failure with a fully staged verified bundle rolls back the published root. There are zero new native launches or protected accesses.

The guarded publication proof executes with macOS CPython 3.14. The existing measurements ran in SOLIDWORKS 2026 SP05.2 on Windows. Every publisher must reproduce the exact measured hashes with its own runtime and encoded locator.

The CLI reproduced all 14 measured files in the same four bundles.
An alternate logical root refused before any file publication in each case.
Strict rereads recovered the actual component definition names and the
local placement order from each file header, active configuration and
reciprocal reference. The native XML index legitimately mirrors the assembly
root name in each model row. The reader determines the titles from the owned
files without changing the measured archive.
[CLI and reread evidence](../measurements/2026/SdkMeasuredNestedCli01.json)

Strict reads of the three dimensioned leaves now restore both linked sketch
lengths and the separate boss depth. Analytic body topology and mass
properties agree with their measured native geometry.
[Dimensioned leaf readback](NestedDimensionedLeafRead2026.md)

On Windows a native locator must agree with the resolved physical output.
The guest probe accepted the derived and identical explicit locators and
rejected a same-basename override in a different folder.
[Windows locator proof](../measurements/2026/SdkNestedWindowsLocator01.json)

The review stack on foundation `a85465a83ae0f1c981d55aa4f8a5b9055f82cabb` uses Git source tree `242dba95c2f7b0b5f4de9dc20ec95d5888125961`. Its complete 44-process disclosed assembly proof reproduced the same receipt digest and all fourteen measured file hashes. The exact-rational standard views preserve these measured bytes. The native half-angle cosine rounds to `0x1.6a09e667f3bcdp-1`, which was also the original macOS result for these receipts. [Standard view rounding](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Presentation/StandardViewRoundingChangesHashes.md)

Both prior standalone part stream cases and both measured part CLI cases returned the same recorded case rows on this stack. The reruns used the original disclosed `SdkDefaultPartNative03` inputs. The [standalone stream probe](../../tooling/sw2026/CheckStandaloneMeasured.py) produced SHA-256 `589bb9a3cf47f300eab9c6a82480836116ec2e1f6306cbc5a270b4b35b250fcb`. The [part and CLI probe](../../tooling/sw2026/CheckMeasuredPartWriter.py) produced `bc925ba9f431a5e88ab4c4e07e4f7e89684578e7d1f2a7aae26d3fc823a8cfd2`. Those calls use the foundation's own part measurement, stream staging, CLI implementation and view generator.

```sh
python3.14 -I -B re/tooling/sw2026/nested_delivery/ProveMeasuredNested.py \
  --workspace DISCLOSED_ORACLE_PARENT --output NEW_PROOF_JSON
python3.14 -I -B re/tooling/sw2026/nested_delivery/ProveMeasuredNested.py \
  --workspace DISCLOSED_ORACLE_PARENT --receipt-case SdkNestedNeutralNative03 \
  --output NEW_MEASUREMENT_JSON
```

The digest-only protected outcomes record the complete bundle manifest and native phase pins for their five- and six-file trees. They omit the ordered individual member rows and the logical namespace this gate requires. A protected exporter must verify the existing guest-local BuildLock and full cold, edit and reopen observations against those public pins. It must join every measured definition to its exact generated digest and size, logical basename and selected configuration, ordered direct child identities, common epoch and actual root namespace, then bind the four clean phases to the same report. A phase that lacks an observed active or referenced configuration needs that specific native observation before the member can qualify. The disclosed proof grants no new protected-route credit. [Protected native summary](../measurements/2026/SdkSealedNeutralNestedNative01.json) · [Protected parity summary](../measurements/2026/SdkSealedPublicNestedParity03.json)
