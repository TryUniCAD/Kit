# Saved SOLIDWORKS 2026 inward open-shell readback

The #121 takeover owns this bounded saved-part reader on
`codex/solidworks-open-shell-typed-read`. Its dependencies are the typed
edge-reference and planar-body readers in [#240](https://github.com/TryUniCAD/Kit/pull/240)
at `48da1cc86a14490a10253ffe2782d7cf2415d895` and the shared shell archive
checkpoint `798e016e18dbf8321f05d7e84a5c13dd3b6ee568`. The source-authoring
and edit oracle belongs to [#250](https://github.com/TryUniCAD/Kit/pull/250).
The scoped reader is in [#255](https://github.com/TryUniCAD/Kit/pull/255).
Hosted acceptance remains pending on the repaired queue candidate.

The disclosed receipt SHA-256
`d469a4d75549f1c95948047264c118adadb3b843b3376218140baa61c752987b`
pins SOLIDWORKS 2026 SP05.2, executable build 34.5.2.0604, healthy reference
controls and the actual initial/edit/reopen sources. The source-only protocol
records that acquisition in
[OpenShellSourceLock2026](https://github.com/TryUniCAD/Kit/blob/84d925a36c79c2b3124aba3ac06830c95297bca1/re/solidworks/records/OpenShellSourceLock2026.md).
The [linked archive replay](../measurements/2026/OpenShellTypedReplay01.json)
consumes and reproduces CMgr, Config-0 and ResolvedFeatures byte for byte
for both complete disclosures. The earlier numeric observer independently
records 30 exact linked research streams.

| Source state | Stored `D1@OpenShell`, metres | Active partition mark | Volume, mm³ | Area, mm² | Centre Z, mm |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original | 0.0028 | 15 | 18559.408 | 13783.12 | 10.810327743 |
| Edited and saved | 0.00353 | 20 | 22690.287908 | 13519.3272 | 11.032153046 |

The linked manager's `f360.f450` entry names the same live atom used by the
stock's `f528` and the shell's `f538`. The atom and the manager record retain
separate initial and modifying feature identities. Each feature's partition
mark belongs to its actual mapped object. The active world mark corroborates
the shell mark. The saved BODY's attached `BODY_MATCH`, `ATOM_ID_2001` and
`LAST_BODY_MODIFYING_FEATURE_ID` corroborate the archive stamp, atom and last
modifier. The attached UTF-16 body label belongs to that same BODY.

The `f828` list owns one local component face. Its terminal role, four
side references and actual earlier feature creation event agree with the
stock's typed chooser entries and closed four-line sketch. The separate
`f848` auxiliary edge must have the same local body and producer ownership
and supplies no removal role. The original and edited
`f818.f850[0].o.ff0.f28.f58` values are the live thickness. They agree
exactly with the linked numeric display cell. The other saved display
copies can round to an adjacent representation. The millimetre projection
divides by the common forward length coefficient. The edited portable
value can therefore be represented as `3.5300000000000002` mm while the
stored parameter remains exactly `0.00353` m.

The normal strict SDK verifies the saved active body's 11 faces, 24 edges,
16 vertices and closed shell. Each plane and line carrier owns its actual
trims or vertex interval. The top rim has a distinct inner and outer loop.
Volume and centroid follow the signed ring geometry. Surface area follows
the per-face rectangle and rim geometry. Those measures agree with the
prior native phases to six significant figures. The one-to-one assignment
of all corners also proves the extent within the common coordinate
tolerance. An earlier exact bounding-box comparison conflicted with that
rounding budget. [Corner tolerance gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Inspection/ShellBoundsRoundoff.md)

Run the [guarded proof](../../tooling/sw2026/shell_source/CheckSavedShellRead.py)
with CPython 3.14 in the isolated checkout, supplying the exact disclosed
directory and a fresh output path.

```sh
python3.14 -I -B re/tooling/sw2026/shell_source/CheckSavedShellRead.py \
  --disclosure /path/to/Disclosure --check-deltas --output /tmp/KitSavedShellRead.json
```

[SdkSavedOpenShellRead01](../measurements/2026/SdkSavedOpenShellRead01.json)
records the two strict modes and the neutral JSON round-trip in three
fresh processes with the L1 control. The independent L1 projection
has the same JSON digest as #240 and retains its known packaged layout
reads. Neither shell worker opens files after imports. A separate execution
of the existing [warm chamfer control](../../tooling/sw2026/CheckWarmChmfBoundary.py)
preserves its strict refusals, permissive geometry and both payload digests.

The contrast worker changes one typed relationship at a time in transient
in-memory containers. It rejects two caps, an outward switch, a foreign
producer, a mismatched auxiliary atom, a changed thickness cell, a
stale active partition and a mismatched manager owner. Both source files
and their receipt are verified before inspection. All source and contrast
bytes stay outside the repository and no measurement is attributed to the
contrasts. These sources lack admission as tracked assets for the general
corpus worker. The guarded probe supplements that pipeline with exact
disclosed-file and archive-owner assertions.

## Saved rollback and shared queue coverage

The [disclosed rollback study](https://github.com/TryUniCAD/Kit/blob/9810079614b14edd7ed61101b2505bad9dc94b09/re/solidworks/records/OpenShellRetainedRollback2026.md)
pins the complete typed transaction proof to two byte-exact native streams
and the shared retained decoder at
`0167c3e33a045b82fb9ac17a5aa10560b2070ba8`. The ordinary shell reader now
uses that decoder with the actual activation, stock and shell markers
from the linked archive. It follows the preceding mark chain through the
selected shell, retained stock, activation and initial states. The same
body slot and atom must resolve on either side of the shell. The stock
controller must own body creation. Both older states must be body-free.
The [historical face check](../../../src/convert/adapters/solidworks/Core/TypedResolved/Shells/History/CheckStockFaces.py)
matches both cap and all four wall keys to actual typed trims and the
earlier sketch lines. The selected top cap must be an actual restored
record. The active rim can share its key. The legacy delete-only path
continues to require its own selected deletion.

Design-only reads apply the same checks before omitting the boundary and
raw payloads. Full reads preserve those payloads for inspection and the
portable conversion gate still refuses retained payloads. Raw extraction
is a separate inspection route. The
[follow-up SDK proof](../measurements/2026/SdkSavedOpenShellRead02.json)
repeats both strict modes with the exact native files and L1, and pairs
the unmodified original active payload with the unmodified edited
rollback. Both strict modes refuse the conflicting history. Permissive
inspection retains its unresolved native feature in that contrast.

The [shared queue test](../../../tests/Convert/Solidworks/Partition/ShellCacheTests.py)
launches independent retained-history and geometry workers. The
history worker uses the tracked OneLights active and history digests from
the existing partition controls. It checks the four stage identities,
retained BODY slot, row counts and rejection of mismatched selectors.
It also checks that the existing L1 transaction still passes the
delete-only profile. The geometry worker encodes and decodes a distinct
authored shell with an exact extent and two controlled shifts. The
existing 16-ULP budget accepts the observed
`1.4210854715202004e-14` mm extent difference and refuses
`2.8421709430404007e-13` mm. Both workers have zero data reads after setup.
[Shared process receipt](../measurements/2026/SdkOpenShellReaderParts01.json)

At the reader's original revision, the tracked SOLIDWORKS examples contain
57 files tagged mo14000, one tagged mo18000 and eight tagged mo19000.
None of the eight has a shell feature. The full SDK shell positives therefore
use the two external, digest-bound disclosures and the shared queue uses
tracked and independently authored component inputs. The native source-only
lock and native fresh-generation requirements remain separate from this
reader regression. The archived evidence represents a single geometry and
its saved edit. Protected coverage and native shell writing remain open.
The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
and [reverse-engineering playbook](../../Playbook/README.md) govern the later
native writer and held-out validation.
