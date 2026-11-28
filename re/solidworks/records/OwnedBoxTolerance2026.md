# Authored and stored tolerances for local rectangular solids

Task B04-SW2026-IMPORTED-BODY in [PR #121](https://github.com/TryUniCAD/Kit/pull/121).
The two disclosed FreeCAD boxes have one baked feature and one uniform
positive tolerance on six faces, twelve edges and eight vertices.
Their earlier generated parts passed the controlled open, rebuild, save
and fresh reopen lifecycle on SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`.
[Source ownership](../measurements/2026/DisclosedBakedFcstdOwners01.json) ·
[Native lifecycle](BakedLocalToleranceNative2026.md)

| Field | Class | Rule |
| --- | --- | --- |
| Neutral boundary tolerance | Input | Read the common millimetre value from the actual face, edge and vertex records of the axis-aligned box. All 26 records must agree. |
| Local transmit tolerance | Derived | Divide the input by 1000 and encode the resulting binary64 length in each linked face, edge and vertex cell. Validate its range with the shared tolerance decoder. |
| Untoleranced default | Constant | Use the format's missing sentinel for local cells with an ordinary untoleranced recipe. |
| Saved face tolerance | Input | In the measured saved profile the same positive length persists in all six face records. |
| Saved edge and vertex tolerance | Volatile | SOLIDWORKS emits the missing sentinel for those 20 records on the measured save path. The neutral reader represents these stored unset values as zero. |

The shared part builder supplies the lengths while allocating the local
body cells. Both neutral requests reproduce the prior native-tested
whole-file digests and all 24 stream digests. The untoleranced controls
reproduce their prior digests as well. Changing the neutral tolerance
changes only the LocalBodies member. The guarded workers consume their
requests in memory, and the existing public writer gate admits the
previously qualified import profiles.
[Shared builder](../../../src/convert/adapters/solidworks/Archive/Partition/LocalPrism/MakeLocalPrism.py) ·
[Construction proof](../measurements/2026/SdkOwnedBoxTolerance01.json)

The strict saved reader checks the rectangular incidence, local feature
and managed atom, kernel name and the selected mark and its activation
predecessor. The ordinary attribute-definition successor outside the
resident transmit is handled by the existing typed saved graph rule.
Both exact native saves now return their complete outward solids and the
six stored face tolerances through the SDK. The measured 22 comparisons
cover both solids' volume, area, centre of mass and extents. Effective
edge and vertex tolerances in the native session require a separate
measurement. These disclosed outputs have zero held-out or intact FCStd
corpus credit.
[Saved tolerance classification](../measurements/2026/DisclosedBakedWarmTolerance01.json) ·
[Shared reader](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/ReadStoredBox.py)

```sh
python3.14 -I -B re/tooling/sw2026/imported_body_source/ProveOwnedBoxTolerance.py \
  --sources /absolute/path/to/DisclosedSources01 \
  --packet /absolute/path/to/NativeBakedTolerance01 \
  --output /absolute/unused/SdkOwnedBoxTolerance01.json
```
