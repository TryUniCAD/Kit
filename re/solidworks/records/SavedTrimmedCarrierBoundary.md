# Trimmed curve records in the saved P03 active partition

## Input and scope

The saved P03 derivative has SHA-256
`dcea552fa4751563c124fb1dc571f3e0b36c0ce37ce39610b45f7717d8687115`.
Its normalized active partition has SHA-256
`af3dd2ac0b09608ef1d48207b0cce8d0a395fdc4adabd97a53522e12c4c9cf56`.
The active payload is 7,110 bytes, with a 96-byte transmit header. All record
offsets in this note are relative to the body after that header. The source
is the already measured 12 mm native save. [Native evidence](https://github.com/TryUniCAD/Kit/pull/338)

The current public reader reaches an unmapped kind 133 before it validates
the full typed graph. Its general geometry path independently reports
`invalid partition topology (missing vertex use)`. This research explains
the typed record boundary and keeps the separate missing vertex evidence.
It uses the active partition only. The ghost and delta bytes retain their
original digests and provenance.

## Kernel class and transfer layout

The licensed kernel reports version 37.01.250 and has SHA-256
`2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969`.
It is the same kernel binary used in the existing
[rectangular partition study](PopulatedPrismPartition2026.md). The installed
SOLIDWORKS bridge modules have different identities from that earlier study.

REA 6.7.0 recorded the kernel identity. Ghidra 12.1.2 identified kind 133 as
the transmittable class `TRIMMED_CURVE`. The effective saved layout is the
same in base 13006 and current 37102. Both descriptors transfer the following
scalars in order:

| Field | Encoding |
| --- | --- |
| `node_id` | 32-bit integer |
| `attributes_features` | Reference class 1019 |
| `owner` | Reference class 1010 |
| `next` | Reference class 1008 |
| `previous` | Reference class 1008 |
| `geometric_owner` | Reference class 141 |
| `sense` | Character |
| `basis_curve` | Reference class 1008 |
| `point_1` | Three binary64 coordinates |
| `point_2` | Three binary64 coordinates |
| `parm_1` | Binary64 parameter |
| `parm_2` | Binary64 parameter |

The first-use transfer comparison selects `ff` for an equal base layout.
The ordinary field reader uses the descriptor to select the destination
member and routes pointer scalars through its reference arm. The static
fixup resolves identifiers into the same members and checks their pointer
classes. The kernel's endpoint accessors use the stored sense. For
literal `+`, they select point and parameter pairs in saved order. The
other branch swaps them. A sentinel point path evaluates the basis.
These are static accessors and transfer facts. The accepted numeric
domain and invocation after active receive remain unmeasured.
[Loader descriptor](../measurements/2026/TrimmedCarrier/LoaderDescriptor.json)
· [Transfer and endpoint evidence](../measurements/2026/TrimmedCarrier/LoaderTransfer.json)

## Record, basis and next boundary

An independent research walker verified the `ff` header and decoded the
first and only kind 133 in the known prefix at body bytes `[1840, 1926)`.
It occupies payload bytes `[1936, 2022)` and has typed index 6, transmitted
reference 7 and `node_id` 211. The next record is the mapped shell kind 13,
index 7, at body bytes `[1926, 1951)`.

The saved body at index 2 names curve 6 in its curve roster. The curve's
owner points back to the body. The next-curve reference names index 46,
which falls outside the decoded prefix. Its geometric-owner field is
null. The prefix contains no edge or fin that names this curve. Complete
edge ownership and the curve's role in the finished body remain open.

Its basis reference reaches line kind 30 at index 50. The line starts at
`(0.04, 0, 0)` metres with direction `(0, 1, 0)`. Both senses are positive.
Evaluating the interval 0 to 0.02 metres reproduces the stored endpoints
exactly. The same ordered pair, `(40, 0, 0)` to `(40, 20, 0)` mm, appears
once among the 12 edges measured in the prior fresh native reopen. This
confirms geometric agreement for the interval on this line. The measured
pair does not resolve an edge's typed ownership of the trim record.
[Geometry comparison](../measurements/2026/TrimmedCarrier/Geometry.json)

The exact walk decoded 84 records before the next unsupported kind 141 at
body byte 3692. It skipped no records and left 55 reference occurrences
unresolved in the prefix. Kind 141 also appears as a reference class in
the descriptor. That declaration alone does not establish a relationship
between this null field and the later physical record.

## Independent controls

Five measured vendor files share the current transmit schema and fully parse
with the existing typed reader. They are the original, a separately saved
control, and three vendor edits that change depth, width and height one at a
time. Their active graphs have 12 direct edge-to-line links each and no kind
133 records. The independently edited 12 mm control's 12 unordered endpoint
pairs exactly match the retained native reopen measurement of the saved P03
derivative. Their distinct wire representations remain evidence. A driving
depth edit alone does not establish a rule for when a trim carrier appears.

## General reader comparison

The general reader uses terminal fin topology to request the eight vertex
attributes `14, 60, 68, 91, 56, 69, 73, 78`. Its scanner retained five of them
and did not supply vertex-use records for `69`, `73` or `78`. The seven
affected edges have scanner carrier attributes `10, 52, 51, 120, 126, 119,
115`. None is the first trim carrier's attribute 7. These are one-based
scanner attributes, and they describe what that path selected. The typed
comparison must establish physical record identities independently.
[General reader diagnostic](../measurements/2026/TrimmedCarrier/LegacyVertices.json)

## Reproduce the offline reads

Use the installed SDK from the clean [PR #340 checkout](https://github.com/TryUniCAD/Kit/pull/340)
with source tree `3739be2f567a3285dd3dc725be9d0d07865a7b18`. Set `$source`
to the native-saved derivative from the P03 native evidence. Use the exact
loader descriptor above. Choose an unused location for each report.

```powershell
python -I -B re/solidworks/TrimmedCarrier/InspectTrimmedCarrier.py --authority $authority --source $source --output $output
python -I -B re/solidworks/TrimmedCarrier/InspectLegacyVertexBoundary.py $sdk $source $legacyReceipt dcea552fa4751563c124fb1dc571f3e0b36c0ce37ce39610b45f7717d8687115 af3dd2ac0b09608ef1d48207b0cce8d0a395fdc4adabd97a53522e12c4c9cf56
```

The repository retains readable format facts and compact receipts. The
private evidence folders retain the exact derivative, full typed trace,
native measurement receipt and licensed kernel analysis. No vendor software
is required to repeat the offline record checks with the retained derivative.
[Compact record and control summary](../measurements/2026/TrimmedCarrier/Boundary.json)
