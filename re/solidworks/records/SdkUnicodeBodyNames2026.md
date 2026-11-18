# Native Unicode body names from agreeing wide owners

The bounded public body-name reader now preserves the full authored Unicode label when the actual archive atom and body-owned implicit UTF-16 value agree. The legacy character name is retained as raw bytes. It is not assumed to be UTF-8 or to represent the complete COM label. The four existing ASCII source states keep their prior exact behavior.

Task: `B04-SW2026-UNICODE-BODY-READ`. Owner: PR #121 configuration/header lane; root independently owns product verification, native authoring and integration. Delivery: PR #121. Dependencies: the actual atom/producing-feature/body-tag join, full active and rollback graph, complete neutral B-rep binding and the exact-build Unicode controls. Exit condition for this reader slice: native/typed agreement on all disclosed labels, strict UTF-16 handling, unchanged unrelated semantics/payloads, rejected mismatched owners and unchanged corrupt-cache behavior through real public process workers. The frozen root replay passed that condition. Named-body writing, the independent cacheless projection and original named H acceptance remain separate work.

## Source and measured ownership

The original getter/setter trace is retained in [NamedBodyUnicodeRead2026.md](NamedBodyUnicodeRead2026.md). The source authoring method is packet SHA-256 `9e8d5bdebea994c735a7aa378146767ccfaf518ba0b3c7001913013ed7ff01a9`. Root completed all eight native processes with healthy controls. The exact native result is SHA-256 `0575f02dcf7c68cf88211710ac3aab3f380164f37282542ea8b4b882e450b2d0`.

The metadata-only [Unicode owner inspector](../../tooling/sw2026/body/InspectUnicodeBodyOwners.py) entered only those explicitly disclosed saves. It parsed every active/history record and actual body-owned attribute using the pinned schema, checked the full solid tree and actual producing-feature/manager alias, and re-emitted all nine complete Config and Resolved streams identically. The frozen correlation result is SHA-256 `194d1616504b78fd63638bb275751a57927fd0526f1ab8f0b1f608faef5d6b4d`; original files remained unchanged. Its companion raw-character inspector uses Latin-1 solely as a reversible research byte transport, not as an asserted name encoding or SDK change.

The six renamed/reopened states show:

| Native label | Archive atom and implicit Unicode value | Legacy `SDL/TYSA_NAME` value |
| --- | --- | --- |
| Accent probe | Exact original Unicode string in both owners | Non-ASCII bytes that reproduce the label under CP1252 and are invalid UTF-8 |
| Greek/CJK BMP probe | Exact original Unicode string in both owners | `?_?????` |
| Supplementary-character probe | Exact original Unicode string, including a valid UTF-16 surrogate pair | `?_??_?`, including two substitutions for that pair |

All three keep `f18c=0`, actual `moNodeName_c.f08`, `SWIMPLICITBODYNAME_ID_U` type 9000 with fields `(10,10)`, a kind-98 first field and null second field. Every explicit character owner remains type 8017, field type `(3,)`, kind 84. `SDL/TYSA_UNAME` is absent throughout. The controls demonstrate that the low-level character-first `gcBody_w::getName` routine is not the complete higher-level COM naming rule. They do not establish a universal ACP or UTF-8 interpretation.

The [lossy-character gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/PartNames/LegacyCharacterBodyNameCanBeLossy.md) records this measured distinction. Raw vendor code and native payloads are not included in the source delta.

## Bounded reader rule

Kind-84 `CHAR_VALUES` now retain bytes inside the typed partition graph. Attribute identifiers keep their existing ASCII decoding. No public document schema changes, mutable namespace state, code-page lookup, CAD runtime or runtime file dependency is introduced.

For a non-ASCII label, the reader requires the real sole manager atom's authored name, strict valid UTF-16 in the actual body's implicit field, exact equality of those two wide owners, and the already established complete atom/feature/kernel/B-rep identity proof. It requires the witnessed character compatibility owner and retains that owner without treating its byte payload as the semantic body name. Invalid or unpaired wide units, nulls, nonprintable text, derived/alternate name state, mismatched wide owners, unknown explicit Unicode/internal alternatives or incomplete ownership preserve the old unsupported path.

ASCII explicit/implicit coherence remains strict. The actual legacy byte payload is not replaced or normalized; `brep_payloads` remain exact. Body IDs, final feature, geometry, dimensions, timeline, source bytes and unrelated metadata retain their original values. A successful Unicode projection reports `qualified_encoding=agreeing_archive_and_implicit_utf16`; ASCII metadata remains unchanged. Both profiles still require a complete body-to-B-rep bijection before replacing the neutral label.

## Independent public process proof

[SdkUnicodeBodyReaderProcess01.json](../measurements/2026/SdkUnicodeBodyReaderProcess01.json) binds root's exact `UnicodeRootReplay04/Replay.json`, SHA-256 `fbc67e97a4d904a2dcc006b942a6e4183ad12f564b52b0c1b6ba3e3f4d790a83`.

The candidate's 4,331-file closure is SHA-256 `c589bf20ed89c6aca3d77564d392bbc1a9ebbc8be52f9427d0ce180411b22637`; its 50-path owned-source manifest is `4edcd6c55bf296c92187bbb3cdc363b49cc4727a4efd5aeef1ab86a178a771f1`. Only six SDK paths change relative to the prior qualified reader. The exact process-tool manifest is `dfd12460e45213d1931087152a60dcd681079c58efd5780c2bb3894d0889b565`.

All 56 fresh Python workers and 115 paired mode comparisons passed across 23 groups. Positive inputs cover the four earlier ASCII states and all nine Unicode baseline, renamed and fresh-reopened saves. The real public `solidworks.sldprt` route was observed in default, repeated default, no-tessellation, history-only and lenient modes. Default/no-tessellation body labels and complete B-rep bindings were exact; unrelated semantic fingerprints and native payload hashes matched the preceding reader.

Eight malformed groups exercise archive/implicit disagreement, wrong atom identity, missing actual output, invalid surrogate, embedded wide null, a different selected cache and a truncated cache. Two compatibility-only groups retain coherent wide owners while varying the unrelated legacy character representation. They preserve the wide label without inventing a codec. Rejected inputs keep the preceding reader's exact document or exception result. These fixtures are research-only controlled mutations, never generated writer outputs or native acceptance inputs.

All public calls attempted zero additional audited file accesses and imported no research serializer. Fixture production executes in separate processes. Source and observer closures were unchanged before/after. Ruff, strict Mypy and strict Pyright passed all six changed SDK sources, with actual-content Black formatting. No unit tests, vendor VM operation, named H read, public writer registration or capability expansion outside this narrow read profile occurred.

History-only body-label behavior, no-cache populated managers, `TYSA_UNAME`-only saves, conflicting wide owners and broader encoding/lifetime states remain explicitly unqualified. These fresh controlled sources are disclosed discovery evidence, not the user's pre-writer original H qualification.

The earlier `Code03` 56-worker result remains retained at SHA-256 `c8847717fa91095ed3dec9facf6226501c285e4748a0031e1665597429e34e52`. Final steering required one single-use temporary to be inlined to meet the declaration size limit. `Code04` changes no scope or behavior; root repeated the full matrix, and all 46 public worker reports are identical to their Code03 counterparts. All six delivered sources pass steering and the donor scan.
