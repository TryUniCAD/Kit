# Strict native-saved circle readback

Task `B04-SW2026-CIRCULAR-BOSS` in PR #121. This main-target follow-up
starts from the measured cold circle writer `f86f6ac5fd0e6cfb1e9d55767dc6d7cd461bbc5c`
and its scoped review repair `fd2de84904eb048347413e75e51d75ed33d49c9f`.
The source is the disclosed diameter beta cohort. The source [native
lifecycle evidence](../measurements/2026/SdkCircleNative01.json) and all
saved files are unchanged. No new SOLIDWORKS or held-out session ran.

## The linked owners

| Confirmed owner | Verified rule |
| --- | --- |
| CMgr `moLinkedAtomIdNode_c`, schema 1 | Its initial i32 precedes two counted `su_CDWordArray` windows. Four following unsigned-count lists pair a signed key and a typed object tag. `moExtObject_c` and its shared path/name handles reuse the standalone header field order. |
| CMgr linkage | All saves end the 1-based manager map at 22. `f658=0` across all three. The regular MBS suffix keeps its existing scope. |
| Config-0 | The existing direct sheet master and populated derived cache grammar suffice. The map ends at 122. The actual atom object under slot 58 carries live body ID 101 and creating feature ID 20 in both `f130` and `f12c`. |
| ResolvedFeatures | The extra Notes Area folder, saved one-chain contour, body chooser, feature and surface references and partition marks use the existing typed layouts from aggregate `49dcac548fff89b914dd2cd6ae33c6df58b69912`. The main-target extraction adds only the exercised branch deltas and required owner classes. The inherited counter is 122 and the terminal counter 278. |
| Sketch and first blind end | The circle's typed radial display resolves to the actual sketch value's `f58`. The live forward end `f818.f18` follows the actual local depth display link to its own `f58`. The saved `f28/f48` end reference lists are present and empty. The inactive `f20` is a different owner and remains 17.825 mm across the edit. The state guards require a whole forward blind boss with no selected scope or active draft. |
| Physical active partition | The boss `f528` is the same Config object and its `f498` independently names that atom. The raw kernel shell 7, owner 3, region 38 carries 101. Three actual source faces and both closed circular edges remain in the public B-rep. The cylinder's stored axis is negative Z. The verified datum normal is positive Z and the planes remain at zero and the live positive depth. |

[Prior independent saved radial grammar](https://github.com/TryUniCAD/Kit/blob/49dcac548fff89b914dd2cd6ae33c6df58b69912/re/solidworks/records/SdkSavedRadialRead2026.md) ·
[Prior native metadata ownership](https://github.com/TryUniCAD/Kit/blob/49dcac548fff89b914dd2cd6ae33c6df58b69912/re/solidworks/records/SavedPartMetadata2026.md)

The saved `f20` value and chooser bounding centers are insufficient to
infer current geometry. Both stay at their first-save state when the live
depth changes. The validated cylinder and body atom provide the physical
comparison. The public reader retains the stored B-rep and computes analytic
volume, area and centroid only after that comparison. Exact wire inputs
remain visible as provenance. Screens and later unrepresented source state
retain their existing behavior.

## Verification

```sh
python3.14 -I -B re/tooling/sw2026/CheckSavedCircleRead.py \
  --packet /Users/odin/Documents/UniCAD/Oracle121Takeover/SdkCircleNative01 \
  --output /tmp/UnusedSavedCircleRead.json
```

The [host process receipt](../measurements/2026/SdkSavedCircleMainRead01.json)
binds three fresh processes, six normal SDK reads with and without B-rep,
and nine byte-exact linked stream replays. It validates the complete
binary64 parameter linkage, the actual neutral fixed center, the live
first end, and the unchanged source B-rep face/curve/edge inventory.
The underlying native terminal and both healthy brackets are verified by
their prior exact digests.

The measured cold circle and both plain-writer controls still emit their
recorded complete hashes. Strict public reads of the unrelated native-saved
Skew and Step parts preserve their full neutral JSON. The compatibility
comparison fixes the Python hash seed to preserve set ordering
and has SHA-256
`95ca16392eedd2a558e5e0b578f09a9cdb3a8e39effc021cabcfcc04c34acefa`.

| Saved state | Diameter and active depth, mm | Volume, mm³ | Area, mm² | Centroid, mm |
| --- | --- | --- | --- | --- |
| First save | 22.95, 17.825 | 7373.688714995752 | 2112.5168560166526 | (7.125, -5.675, 8.9125) |
| Edited save and fresh resave | 19.163249999999998, 21.122625000000003 | 6092.227335460804 | 1848.4918136434019 | (7.125, -5.675, 10.5613125) |

The adversarial probe changes the typed output-atom row and separately
supplies the unedited raw partition with the edited feature archive.
The first change leaves the compatibility projection with an explicit
typed-owner diagnostic. The second refuses strict read at the physical
radius comparison. A non-strict read retains the fallback geometry
with a diagnostic and no computed exact body measurements.
These containers exist only in process memory. They are input controls,
not production output or stream templates.

Scope is the ordinary forward Front-plane diameter saved boss. Reversed,
radius, alternate ends, selected bodies, additional source owners, and
native-saved read-to-write publication remain separate.

## Scoped review follow-up

The three disclosed native files above still give six strict reads and nine
exact manager, configuration and resolved stream replays. The inactive
length is present in the boss step attribute
`solidworks.inactive_blind_depth` in both geometry and design-only reads.
It is archive parameter 258, attached to dimension 257 through
`f818.f20`, with the binary64 value `0.017825` metres in `f58` across all
three files. The owner span moves with the native save from
`[12465,12508)` to `[12559,12602)` to `[12565,12608)`. The active
depth and radial parameters are independent of that slot. No second
editable extrusion end is asserted.

The saved physical body now acquires its design identity after both the
actual raw shell atom and the cylinder agree. An in-memory contrast retains
the exact original physical partition with atom 101 and changes the two
agreeing logical claims to 102 through the typed archive codecs. The
strict path refuses the atom mismatch. The permissive path still retains
the raw physical body and payload, with no design association, attributed
topology or body measurements. The original stale radius and crossed producer checks are
separate. None of the contrasts is published or passed to SOLIDWORKS.

[Updated guarded read receipt](../measurements/2026/SdkSavedCircleMainRead02.json)

The hosted process coverage uses two independently saved, disclosed CAD
controls. Its first and edited-reopen files have SHA-256
`f85b89e5920cfdb922657c57fc92d92c1e039db3e95286ad6e0f8e4c5712b6fc`
and `c8e6326464e2de7fd15d56a2e34c68320f7494cb3b6faa4a6924867619d16784`,
respectively. Both are bound to the original phase observations before
the SDK worker uses them. These are read controls in `re/` only and
do not feed production generation.

```sh
python3.14 -I -B re/tooling/sw2026/CheckSavedCircleRead.py \
  --fixtures --output /tmp/UnusedSavedCircleFixtures.json
```

The cold forward diameter candidate separately regenerated the recorded
whole archive through the direct and registry paths from strict full and
design-only reads. Its model-only planner consumed the actual typed radial
and depth owners. The complete regenerated readback is compared before the
existing per-file native evidence gate. The cold archive carries no saved
partition, unlike the native-saved inputs above.

[Cold republication receipt](../measurements/2026/SdkMeasuredCircleRepub01.json)
