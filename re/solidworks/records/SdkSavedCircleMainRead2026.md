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
