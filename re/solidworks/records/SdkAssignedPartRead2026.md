# SOLIDWORKS 2026 saved material assignment in the normal SDK

The `B04-SW2026-NAMED-MATERIAL` tranche belongs to the
[PR #121](https://github.com/TryUniCAD/Kit/pull/121) takeover. The
isolated reader uses main `c8d85d713dc357770115329e9f1bcb027dbfca4f` and
the existing [typed archive proof at aggregate `0167c3e3`](https://github.com/TryUniCAD/Kit/blob/0167c3e33a045b82fb9ac17a5aa10560b2070ba8/re/solidworks/records/SdkAssignedMaterialRead2026.md).
The exact visual texture, bounded ghost and manager atom/file leaves come
from [PR #232](https://github.com/TryUniCAD/Kit/pull/232),
[PR #238](https://github.com/TryUniCAD/Kit/pull/238) and
[PR #239](https://github.com/TryUniCAD/Kit/pull/239) respectively.
Local dependency commit `c795755f4941a83d7ab50c1bc68f1b54403adf6a`
contains just those five unchanged files. The existing default archive
contexts retain their original layouts.

## Bound owners

| Claim | Validated link |
| --- | --- |
| Selected configuration | The sole CMgrHdr2 directory row matches the mapped CMgr configuration and the part geometry stamp. Both `f360` and `f368` point to the actual `f370` directory member. |
| Physical density | The mapped part hatch adjoins its `f1420` material and nested density. The density is positive, finite, free of alternate links and equal to the active configuration density `fc50`. |
| Material identity | The part and configuration own their own visual nodes and hatch records. Their catalog, name and decimal native ID agree. The bounded texture layout is decoded without assigning texture semantics. |
| Active solid | The live part atom in `fd88` supplies the key of the actual single `fb00` row. The CMgr configuration `f450` link independently ties the same atom to the owning feature. The physical shell's native body attribute matches that atom. The SDK body's final feature must identify the same owner. |
| XML corroboration | The actual BOM-marked material tree owns one matching classification row, selected configuration association and physical density. The core parser consumes that stream from memory. |

Both public strict read modes return the same physical assignment on
the body's `solidworks.assigned_part_material` attribute. The two
disclosed material identities each retain their measured density, 2700
and 7858.000032 kg/m³. All seven sources bind the actual atom 101 and
producing feature 34. The active shell's owner is body 3. The world's
first body is a separate wrapper at index 2.

The required RGBA of `MaterialRecord` has no proved replacement for
the [distinct saved color domains and swatches](https://github.com/TryUniCAD/Kit/blob/0167c3e33a045b82fb9ac17a5aa10560b2070ba8/re/solidworks/records/AssignedMaterialAppearanceProjection2026.md).
The body attribute therefore carries the measured physical evidence.
Appearance, complete catalog properties, configurable body overrides
and writer support remain unresolved. A source with material XML but
incomplete or contradictory ownership receives
`sldprt.material_assignment_unresolved` while retaining its previous
geometry and features. The successful physical read still diagnoses
the unresolved domains. The ordinary path is unchanged when the
material stream is absent.

## Verification

```sh
python3.14 -I -B re/tooling/sw2026/materials/ProveSdkNamedMaterial.py \\
  --source /absolute/disclosed/SdkNamedMaterial01 \\
  --output /tmp/UnusedSdkAssignedPartMaterial01.json
```

The [guarded receipt](../measurements/2026/SdkAssignedPartMaterial01.json)
binds the seven exact disclosed files and one pristine unassigned
control to earlier SOLIDWORKS 2026 SP05.2 observations. The supervisor
reads only those files and their pinned prior receipts. It compares
eight fresh SDK processes with eight baseline processes derived from
the exact main commit. The prior SDK fields agree in all sixteen
mode comparisons after removing only the new material evidence and
its derived semantic fingerprint. Both unassigned modes reproduce the
complete earlier SDK document digest. The workers separately count
reads of the packaged legacy grammar. The guarded reads and owner
checks record zero other runtime external accesses.

The contrast refuses wrong or duplicated XML owners, changed density,
wrong framing, a missing partition and a different physical atom.
Native publication attempts leave the destination stream empty.
The queue checks the assigned-material diagnostic against a tracked
unassigned source and a transient invalid material claim in both
strict modes. Its fixture requires no added CAD asset.

The SDK source tree is `7163bbf455aab4e5171676ce99798516d305fd1f`.
Fresh macOS Python 3.13 and 3.14 workers produce the same receipt
SHA-256 `7363e1504e5a0a86d6b34dc14c1dbcdf404f9f0a3e493fa984d5e90578dff6dc`.
This result measures saved-reader behavior. It adds zero native
lifecycles, zero held-out credit and zero qualified writer profiles.
