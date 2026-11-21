# SOLIDWORKS 2026 saved part Definition view

Task `B04-SW2026-PART-DEFINITION-VIEW` extracts the saved orthographic
view projection from PR #121. The delivery uses accepted main
`2c3330b3e79cb199655e590eb63458f5bef316f2` and its existing whole
part Definition codec. Six source modules carry the bounded camera
contract. `ReadPartView` connects it to the complete typed stream.
[Change entry](../../../Documentation/Changes/Solidworks/Inspection/Presentation/SolidworksSavedPartView.md)

## Native owners

The version-19000 `uiPartDoc_c` root owns two ordinary
`mgXform_c.restore` records. The `fae8` orientation uses an optional
nine-coefficient binary64 matrix and fixed neutral affine components.
The `faf0` owner carries native pan in `f58/f60/f68` and positive zoom
in `f70`. Both records use zero mode flags in the admitted scope.
Without a matrix record, the orientation is identity. The matrix
must be orthonormal and right handed. The archive reader preserves
canonical presence and the actual binary64 values.

The original loader evidence binds the `uiModelDoc` getters at
`0x49787270` and `0x497871a0` and the ordinary `mgXform::save`
field order. An independently owned user environment can supply a
different active window pose. The present reader projects the
document pair and leaves window selection to that owner.
[Field and role evidence](https://github.com/TryUniCAD/Kit/blob/646abf82c9ca3c511fe742386980fd6fea73fb8e/re/solidworks/records/ThroughAllSourceView2026.md)
· [Prior guarded source results](https://github.com/TryUniCAD/Kit/blob/646abf82c9ca3c511fe742386980fd6fea73fb8e/re/solidworks/measurements/2026/ThroughAllSourceView01.json)

## Direct archive evidence

| Case | Definition bytes | Orientation | Zoom | Saved user environments |
| --- | --- | --- | --- | --- |
| L1 boss native save | 3,816 | Explicit native matrix | 5.900297031550575 | 1 |
| OneLights native save | 3,672 | Implicit identity | 3.3533877980364655 | 1 |
| ConcaveOwned verified imported-solid control | 459 | Implicit identity | 1.0 | 0 |
| Independently authored Definition | 535 | Quarter turn with signed zero | 0.625 | 0 |

Three input workers verify the checked-in part and Definition hashes.
The complete Definition reader allocates the existing typed graph.
The wrapper projects the two actual root fields. Each worker compares
all thirteen pose scalars as packed binary64 values and repeats the
existing typed Definition writer for complete stream equality.
The two native source cohorts come from separate authorship records.
[L1 Definition](../measurements/2026/SdkOrdinaryPartDefinition01.json)
· [OneLights native save](../measurements/2026/ConfigSceneCounts01.json)
· [ConcaveOwned provenance](../measurements/2026/LocalImportReadbackFixtures01.json)

The fourth worker constructs a Definition from independent values,
including a signed-zero coefficient and signed-zero pan. A fresh
receiver checks exact projection and full typed re-emission. Eight
other complete typed definitions refuse unsupported perspective,
pan orientation, hidden orientation translation, a negative-zero
orientation offset, redundant explicit identity, reflection, shear,
and zero zoom. Three separately framed inputs preserve NaN pan,
positive infinite zoom and negative infinite matrix coefficients
through the full Definition codec. The pose projection refuses each
nonfinite scalar. Two further contrasts refuse an alternate version
and trailing data. All five workers report zero guarded external access.

Run the [process probe](../../tooling/sw2026/CheckSavedPartView.py) from the checkout root.

```sh
python3.14 -I -B re/tooling/sw2026/CheckSavedPartView.py measure
```

The [receipt](../measurements/2026/SavedPartViewRead01.json) binds
exact stream and pose digests, diagnostics and the measured source
closure. The [queue case](../../../tests/Convert/Solidworks/ArchiveDefinition/SavedViewTests.py)
uses the same subprocess entry point. This is saved archive
inspection. Public presentation transfer and native visual
acceptance require independent evidence.
