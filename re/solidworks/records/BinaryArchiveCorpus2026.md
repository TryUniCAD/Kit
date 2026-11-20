# SOLIDWORKS 2026 binary archive round-trip census

Task `B03-SW2026-ARCHIVE`, owner `/root`, PR #121. Two independent host
processes read the same 80 disclosed parts and eight assemblies as the
KeyWords audit. Each input comes from a pinned Git object at
`5554733fde548afabdc6db221f387163d15e9497`. The measured codecs are
pinned to `ae9ca38d3da61e40379e693476126eec5d2030f0`.
[KeyWords comparison](KeywordCorpusFraming2026.md)

| Scope | Attempts | Exact with complete consumption | Exact without raw fields |
| --- | ---: | ---: | ---: |
| Fifteen common binary streams | 1,320 | 1,320 | 1,320 |
| Assembly MatesList | 8 | 6 | 6 |
| Total | 1,328 | 1,326 | 1,326 |

The common set is CMgr, CMgrHdr2, Config-0, Config-0-ModelHeader,
Config-0-ResolvedFeatures, CusProps, Definition, eModelLic, Header2,
ModelStamps, SwDocContentMgrInfo, VisualStates, DLUpdateStamp, Biography
and History. ResolvedFeatures uses the real configuration map. The
Definition SDK reader consumes its complete layout and the writer emits
the documented release CLSID for each model kind. The independent
legacy research round trip also matches every Definition. Its single
eight-byte raw field per direction is the fixed CLSID suffix, which the
SDK represents through the actual model class.
[Definition rules](SdkModelDefinition2026.md)

All 88 VisualStates streams consume and re-emit their exact bytes with
typed fields. The recorded schemas still include provisional classes
and layout branches. The remaining 1,238 exact comparisons used no
provisional schemas. The six successful mate comparisons are empty
lists. For each, the SDK first re-emits the original Config-0 and
ResolvedFeatures, then the actual inherited mate map and complete
six-byte list.

The two initial occurrence assemblies, `A0_one.SLDASM` and
`A1_two.SLDASM`, reach the SDK's unsupported
`moHistoryCompItemData_c` schema-one context before the mate stream.
The research registry decodes both ResolvedFeatures streams exactly.
SDK context support and subsequent MatesList acceptance remain open.
[History component context](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/HistoryComponentReadContext.md)

Run from the checkout retaining the recorded codec tree:

```sh
python3.14 -B re/tooling/sw2026/AuditArchiveCorpus.py \
  5554733fde548afabdc6db221f387163d15e9497 \
  ae9ca38d3da61e40379e693476126eec5d2030f0 \
  /tmp/UnusedBinaryArchiveCorpus.json
```

The [numeric receipt](../measurements/2026/BinaryArchiveCorpus2026.json) has
SHA-256 `06b4b858876845880c81260cb958dd9bec08b252c9d2022ab5d9a3582b227639`. It records stream hashes,
linked map counts, schema state and the two refusals. This census starts
zero native processes, reads zero sealed inputs and publishes zero CAD
outputs. Derivation of model inputs, native writing and original FCStd
conversion qualification have separate acceptance gates.

The [subsequent SDK history-component port](SdkAssemblyHistoryComponent2026.md)
reproduces all six linked streams on those two controls, including the actual
three-mate graph in A1. The census above retains its original codec revision.

## Follow-up after SDK assembly history admission

Two independent runs at codec revision `698fa68a6a9990bc4c125d2fea36c3e443a14445`
reproduce both previous mate refusals and all other measured streams.
All 1,328 comparisons on the 88 original inputs now consume the complete
stream and re-emit exact bytes through typed fields. The eight mate
streams include A1's three ordered mates. A1's display distance uses the
counted binary64 codec. The audit recognizes that typed field by its
element count, type and observed length. Its writer encodes the individual
scalars. All 88 VisualStates streams still carry provisional grammar,
leaving 1,240 comparisons across the other roles with confirmed schemas.

The complete repeated report SHA-256 is `3b1f135b6324f4fa069ff6123986c54bc89b0c246cb7740d83de20d50126981a`.
The [follow-up receipt](../measurements/2026/BinaryArchiveCorpusAfterHistory01.json) retains the new totals
and the only two changed observations. The original files and the other
1,326 observations retain their exact hashes and results.

The aggregate rechecked the same pinned cohort after integrating the
accepted standalone header codec. At `14c1d82cf5cba0c17ba14cf7e630bdd1660f084f`
all 1,328 measured streams still replay exactly. The 88 VisualStates
paths retain their provisional schemas. [Post-merge receipt](../measurements/2026/BinaryArchiveAfterStandaloneHeaders01.json)

After integrating the accepted counted-row codec, all 88 per-file
reports match the preceding audit. The typed wire forms preserve
1,328 exact stream comparisons and the same schema boundaries.
[Counted-row integration receipt](../measurements/2026/BinaryArchiveAfterCountedRows01.json)

After integrating the accepted archive body values in PR #177, the
same 88 per-file reports agree exactly with the counted-row audit.
The 1,328 exact binary stream comparisons and 1,240 comparisons without
provisional schemas remain. A separate scan found zero recorded
payloads in the 4,962 production Python files of that aggregate snapshot.
[Body-value integration receipt](../measurements/2026/BinaryArchiveAfterBodyValues01.json)
