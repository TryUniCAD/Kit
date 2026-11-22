# Measured ordinary local linear pattern delivery

Task `B04-SW2026-LOCAL-LINEAR-PATTERN` is an independent extraction from
[PR #121](https://github.com/TryUniCAD/Kit/pull/121). The baseline is
`e5294382aad0c04ba26554dfe381fd03daec110a`. The measured scope is one local
positive forward plate, one joined forward rectangular seed, a finite
Top/Right hinge and acute Back-annotated angular plane, and one signed
single-direction linear pattern. The source specifies a single active
configuration, 2–8 disjoint interior instances, independently owned
vertical and horizontal sketch relations, distinct stock depths, and
driver-owned count and spacing. The final body is derived from these
typed records when physical geometry is absent.

## Native qualification and custody

The two disclosed complete files were built from neutral model and typed
source presentation in `GeneratedLocalPatternNative02`. The original
native batch used SOLIDWORKS 2026 SP05.2 (`34.5.2.0604`), executable SHA
`3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`.
Its two controls bracket four separate candidate processes. Both
candidates opened and rebuilt without reported errors or warnings.
Native D1 count and D3 spacing were observed as live editable pattern
parameters. The stock feature depths and angled datum constraint were
measured as separate native relationships. The batch changed D3 from
18 to 24 mm in A and from 19 to 22 mm in B. Each edit rebuilt and saved,
and each separate reopen matched the stored edit. The original-to-edit
and reopen phases have 55 and 33 numeric checks per candidate, with no
controller diagnostics. A SOLIDWORKS edit/save and a Kit publication
after a neutral edit are separate operations.

| Candidate | Exact original archive | Bytes | Original topology | Volume in mm³ | Area in mm² |
| --- | --- | ---: | --- | ---: | ---: |
| ColdRaisedPatternA | `f7e5290dfda2cd2aedfc281ea8ee6275fd1214fc011bcda51f88d43d8cc4356f` | 10474 | 1 solid, 21 faces, 48 edges, 32 vertices | 107715 | 36638 |
| ColdRaisedPatternB | `032c9c5696a4b97a9a5c5178147cb8443b90a6350588154dec693ff56d372754` | 10461 | 1 solid, 26 faces, 60 edges, 40 vertices | 83836 | 36275 |

The [packet](../v2026/corpus/linear-pattern/MeasuredCold01/Packet.json)
binds the original file SHA-256 values, executable and build evidence.
Its SHA-256 is `da60bbfdc5411448b9aa5cd06c2a8772a0e0f2c39efa14ba2dc336c625e32cb1`.
The [terminal report](../v2026/corpus/linear-pattern/MeasuredCold01/Result.json)
keeps the disclosed native observations as JSON. The proof restores
the exact original ordered Windows JSON encoding with two-space
indentation, CRLF and a final newline. Its result SHA-256 is
`ae4f5853e4066a0d3f00cf4cbdaac12797b18c55c268ada6431d7e062bd5d23b`.
The build SHA-256 `b04e279af46524b69a3198c50e2ba06a89702327be1885eb5e2283d82f2d84a3`
owns the [logical stream witnesses](../v2026/corpus/linear-pattern/MeasuredCold01/Streams.json).
The fixtures contain independent authored request values, hashes and
observations. The writer does not consult the fixture directory. The two
exact reports are caller-supplied measurement evidence. Their values
cannot become element geometry, presentation, style or serialized
fields.

## Generative graph and cold source read

The ordinary Config-0, Header2, CMgr, Definition and empty history
emitters are shared. Config-0 required no grafted layout. Resolved
inherits the actual map at counter 94 and completes at 316 in both
disclosed cases. The explicit pattern context introduces the 21 reached
typed declarations and the populated portions of four existing body
layouts. The existing stream order and defaults stay in the other part
route. The typed local atom changes from plate to seed to pattern. Both
stock selectors bind that exact lineage and the real model root. The
native count and spacing drivers own the D1 and D3 records and six
distinct display slots. Ordinary prism and assembled-planar boundary
validation derive one closed solid with the measured volume, area and
centroid.

The two disclosed authored requests use *Back* and *Front* annotations
in different orders. The production reader resolves those actual
annotation views and the dependent angle and pattern displays. Separate
checks cover the base transforms, view aliases, role membership,
and inactive secondary direction. The strict reader also projects the
real two original stock rectangles and their four axis relations, both
independent native depths, directed hinge and angular plane, and both
stock body picks. Each original sketch has two horizontal and two
vertical relations and no sketch dimension parameter. The rectangles'
sizes and positions are authored by their vertices. A valid neutral
input with an added sketch dimension refuses before writing.

Strict reads with `include_brep=False` recover the same features,
dimensions, constraints, selections, configurations, and body metadata.
They omit the derived B-rep and its capability and recompute the semantic
fingerprint for that projection. A recognized cache-free version-19000
pattern with missing typed history refuses in either strict mode.
Permissive inspection can return unqualified native-only history.
A separate same-length keyword caption contrast reaches the final
typed timeline binding after the physical graph has passed. Both
strict read modes retain the owner contradiction as their error cause.
Both permissive modes fall back to the original archive model before
adding derived pattern geometry or claiming typed pattern ownership.

Cold republication regenerates the archive and checks the entire neutral
result against a new strict decode in the same geometry mode. It refuses
any residual readback state absent from that reproduction before requiring
a matching complete-file native receipt.

### Saved pattern read boundary

Two independently disclosed, native-written version-19000 saves from
the prior angular comparison retain 31 timeline rows and one body.
The original has 16 faces. The separate spacing edit has 17 faces and
overhangs the plate. Each positively identifies feature 52 as
`moLPattern_c` and `Feature Type="LPattern"` in the selected Config-0
lane. On this delivery branch the linked reader stops in
`Contents/CMgr` at schema-one
`moLinkedAtomIdNode_c` before it can prove the active history. The
geometry-bearing and design-only strict reads refuse both saves with
the saved-history diagnostic. Permissive inspection preserves the
original model and geometry, and explicit raw extraction preserves the
exact two Parasolid payloads for each source.

The isolated host comparator checked the baseline and current reader
in twelve fresh SDK processes. It also compared a version-14000 part
with five recognized patterns, a version-19000 ordinary blind boss,
and both exact Windows-compressed cold candidates. All four controls
retained their complete read and raw extraction outcomes. This proof
extends the read boundary only. The native archive, publication
receipts and compressor authority stay unchanged.
[Saved intake receipt](../measurements/2026/SavedLinearPatternBoundary01.json) ·
[Prior native angular evidence](https://github.com/TryUniCAD/Kit/blob/97f9910c387490d7f1ba05c9d1fbd913f2655409/re/solidworks/records/SdkWarmAngularPatternRead2026.md)

```sh
python3.14 -I -B re/tooling/sw2026/AuditSavedPatternRead.py \
  --disclosed /absolute/path/to/LinearPatternEnvelope02/DisclosedTrial \
  --compression /absolute/path/to/PatternCompressionTrial01/Alternate
```

The measured historical family has distinct pre-writer locked native
tests on the aggregate branch. The previously locked method, native
observations and later exact SDK comparison remain recorded at
[aggregate evidence](https://github.com/TryUniCAD/Kit/blob/7b202c60e469508e485c59eebf897bc37b5ccd81/re/solidworks/records/LocalLinearPatternPublicParity2026.md).
This extraction's current publication allowlist uses the two disclosed
archives above. It confers no new held-out, FCStd conversion,
or warm saved-source coverage.

## Reproduce

Run these independent process-boundary measurements from the checkout.

```sh
python3.14 -I -B re/tooling/sw2026/CheckMeasuredPattern.py --case ColdRaisedPatternA
python3.14 -I -B re/tooling/sw2026/CheckMeasuredPattern.py --case ColdRaisedPatternB
```

Each process admits the recipe JSON before installing the audit guard.
Each case produces seven exact public or direct publications from the
authored neutral request, the full strict readback and the design-only
strict readback. The registry consumes a design-only snapshot restored
via the ordinary `CadDocument` neutral JSON methods. Strict reader checks
use actual file and memory inputs. Twenty-one refused writer or raw
extraction routes include an unmeasured pitch even with explicit
permissive policy, a forged or missing receipt, wrong clock and locator,
wrong driver ID, extra source metadata on both read modes, an additional
sketch dimension, wrong-path replacement and absent raw Parasolid
payload. Two further strict reads refuse a missing CMgr owner.
Two strict reads also refuse the contradictory keyword caption, and
two permissive reads recover only the native inspection model.
Permissive inspection is exercised separately from the writer and
strict-reader runtime audit.

The complete archives and all ten logical streams match the measured
files, with zero guarded runtime input reads or CAD launches. The
[revision-bound receipt](../measurements/2026/MeasuredLocalLinearPattern02.json)
binds the current scoped evidence and links the
[original proof](../measurements/2026/MeasuredLocalLinearPattern01.json).

Classic zlib 1.2.12 and the measured Windows zlib-ng envelope each have a
separate exact packet and result. Both Windows candidates preserve the
same ten uncompressed streams and passed the native open, edit, save
and reopen lifecycle across six more processes. Seven guarded writer
routes per case reproduced the measured Windows bytes. Crossed packets
and results and the valid classic receipt supplied for a Windows
candidate all refused with unchanged outputs.
[Windows compression proof](../measurements/2026/MeasuredPatternCompressionPublication01.json)
[Procedure and byte identities](MeasuredPatternCompression2026.md)

Warm saved reads, newly
generated edited outputs and dimension-driven stock sketches remain
open in the wider [PR #121](https://github.com/TryUniCAD/Kit/pull/121)
programme.
