# Partition record boundaries and the vertex byte scan

Task `A12b-PartitionRecordBoundary`, owner the retained SOLIDWORKS boundary
verifier, depends on the existing #121 `B04-SW2026-ORDINARY-PART-PARTITION-LOAD`
workstream and its reader-owner coordination with B08. This tranche records
the diagnosis and a concrete existing-helper transformation for discussion.
It does not implement a production correction or claim native acceptance.

## Exact observed scope

The command pins SDK revision `c0a401a607759fb0c2589647c2a22af65ebb7ce1`
and research tooling tree `4503ec0e1e833b443cf111886dff42941f0a1bc4`.
All offsets below are relative to the active payload body after its transmit
header, not to the archive or compressed member.

| Input | Active nodes | Typed vertex/point pairs | Public B-rep | Diagnostic topology F/E/V |
| --- | ---: | ---: | --- | --- |
| Generated four-line `f5647d6c…` | 177 | 8 | returned | 6/12/8 |
| Generated five-line `0cbf1cc4…` | 203 | 10 | absent | 7/15/10 |
| Vendor control `db139047…` | 180 | 8 | returned | 6/12/8 |

All three `ReadActiveNodes` results consume the complete current-schema active
payload and pass `CheckXmtGraph`. The vendor input is the locked P03 baseline A,
Git blob `1de2d0f05f34c4c023f4eaeda7cd4226b06bc813`. It is an independent
reader comparator and is never supplied to a writer.

For five lines, `ScanPartRecords` visits the incidental kind-18 pattern at 988
inside actual kind-17 fin 18, span `[978, 1001)`. Its attribute 83 references
`(1, 44, 11008, 4352, 5120)`. Point 5120 is absent. The true vertex record is
typed index 82 at `[2809, 2837)`, with scanner attribute 83 and references
`(1, 19, 81, 85, 84)`. Its point is typed index 83 at `[2837, 2877)`, scanner
attribute 84. The fin's actual vertex reference names typed index 82.

The pinned source explains the cause: `ScanPartRecords` tries eligible byte
positions, `ScanTopoMut` retains the first accepted attribute with `setdefault`,
and `ParseVertexUse` accepts the earlier candidate. The real later record
cannot replace it. `VertexPointData` then raises `missing vertex point`.
The unchanged payload result is `invalid partition topology (missing vertex point)`.
The public reader returns one body but no B-rep, with its existing environment
name diagnostic. The source bytes are not shown to be malformed by this scan.

## Existing-helper diagnostic transformation

After full current-schema parsing and graph validation, the command walks the
same bytes using `XmtCursor` and `ReadXmtNodeMut` to obtain authoritative spans.
For every kind-18 node it calls the existing `ParseVertexUse` at that boundary
and checks that the attribute and point reference each equal one more than
their corresponding typed index. It builds the whole transient vertex map, rather than selecting attribute
83 or adjusting one offset. A copied `RecordTables` receives that complete map;
the original scanner table and SDK functions are untouched.

Existing `BuildPartModel` then validates all three models without errors.
Only the five-line cohort has a differing selected vertex span. A fresh call
to the unchanged payload reader still returns its original failure. This is
causal diagnostic evidence, not a shipped repair.

Both generated partition members re-emit byte-exact through existing research
structural tooling. The vendor member parses there but its framed re-emission
is not byte-identical; that separate limit is retained in the report. No claim
of vendor-frame replay, complete semantic equivalence or application acceptance
comes from these topology checks.

## Reproduce without native software

Use a clean exact #121 checkout for `$sdk`. A selective checkout can retain
`/src/` plus these three existing research files with `--no-cone`:

- `/re/tooling/sw2026/para/Partition.py`
- `/re/tooling/sw2026/para/Schema.py`
- `/re/tooling/sw2026/builders/EmptyPartition.py`

Apply that sparse specification through `git sparse-checkout set --no-cone`
and `git read-tree -mu HEAD`; do not restore the complete tree. Set `$tools`
to its `re/tooling/sw2026` directory. The command compares imported tooling
against the exact Git objects after line-ending normalization and records
actual physical file digests. It rejects a wrong or modified SDK.

Set `$four` and `$five` to the retained exact generated archives, with their
original sibling `Evidence.json` receipts. Set `$vendor` to the existing locked
capture `re/automation/PairedCaptures/P03/solidworks-db1390476325/P03-solidworks-baseline-a.SLDPRT`.
Use an absent report path:

```powershell
python -I -B re/solidworks/PartitionBoundary/InspectRecordScan.py --sdk-root $sdk --tools-root $tools --four-line $four --five-line $five --vendor-control $vendor --output $newReport
```

The [compact exact report](../measurements/2026/PartitionBoundary/RecordScan.json)
contains all three archive hashes, generated base/request lineage, original
receipt digests, payload hashes and method fingerprints. Private retained
`RepeatOne`/`RepeatTwo` and `FiveLineOne`/`FiveLineTwo` inputs remain unchanged.
The five-line combined `Request.json` has SHA-256 `f76f408a27c36eac1e793faf15391c5a8b46868404296bcf7d431d97879c182a`;
its existing private generation probe has SHA-256 `78633776f509bd1f9537e038df17d191c253db74398a987c818f287863e6890b`.
No native file or installed vendor software is committed by this tranche.

Two final fresh processes reproduced the report exactly. A separate wrong-SDK
process exited 1 without output. These are deterministic offline process
measurements, not oracle acceptance or a held-out writer qualification.

## Reader-owner handoff

The existing SOLIDWORKS active-partition path delegates geometry to the general
byte scanner. Existing `Archive.Partition.ReadActiveNodes`, `CheckXmtGraph`,
`XmtCursor` and `ReadXmtNodeMut` already supply a complete current-profile
inventory and vertex ownership for these inputs. They establish a concrete
candidate transformation to discuss with the #121/B08 owners without another
numerical scan heuristic or new serializer.

The next coordinated exit is a qualified owned integration with process
coverage of the real active-partition public boundary, preserving unsupported
profile rejection and independent controls. It must address ownership and
version limits, additional vertex/surface forms, and unchanged public behavior
outside its scope. This report does not prescribe production layering or
authorize a patch. Native and full-source acceptance remain open.

[Change entry](../../../Documentation/Changes/Research/Readers/SolidworksPartitionRecordBoundaryEvidence.md)
and [specific gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/VertexScanCanMisreadFinPayload.md)
