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

Both public strict read modes return the same physical assignment. The
design body's `material_id` links to the portable `MaterialRecord` and
its `solidworks.assigned_part_material` attribute retains the verified
configuration, catalog and native owner IDs. The disclosed material
identities retain measured densities of 2700 and 7858.000032 kg/m³. All
seven sources bind atom 101 and producing feature 34. The active shell's
owner is body 3. The world's first body is a wrapper at index 2.

The assigned record leaves its color unset. The [saved color domains
and swatches](https://github.com/TryUniCAD/Kit/blob/0167c3e33a045b82fb9ac17a5aa10560b2070ba8/re/solidworks/records/AssignedMaterialAppearanceProjection2026.md)
identify distinct archived render values and require an effective-color
measurement. A source with incomplete or contradictory material
ownership receives `sldprt.material_assignment_unresolved`. A confirmed
physical read diagnoses the remaining appearance and catalog domains.
Native and registry writes refuse either incomplete state before
staging. Full geometry reads reuse the decoded active partition and
read its actual shell atom. Design-only reads verify the same partition
without including its geometry in the result.

## Verification

```sh
python3.14 -I -B re/tooling/sw2026/materials/ProveSdkNamedMaterial.py \\
  --source /absolute/disclosed/SdkNamedMaterial01 \\
  --output /tmp/UnusedSdkAssignedPartMaterial02.json
```

The [typed material receipt](../measurements/2026/SdkAssignedPartMaterial02.json)
binds the seven exact disclosed files and one pristine unassigned
control to earlier SOLIDWORKS 2026 SP05.2 observations. The supervisor
reads only those files and their pinned prior receipts. It compares
eight fresh SDK processes with eight baseline processes derived from
the exact main commit. The prior SDK fields agree in all sixteen
mode comparisons after removing the new material record, body link,
capability and derived fingerprint. Both unassigned modes reproduce the
complete earlier SDK document digest. The workers separately count
reads of the packaged legacy grammar. The guarded reads and owner
checks record zero other runtime external accesses.

The contrast refuses wrong or duplicated XML owners, changed density,
wrong framing, a missing partition and a different physical atom.
The shared queue case uses the [disclosed authored diagnostic part](../v2026/corpus/named-material/AssignedDensityProbe.SLDPRT).
Its immutable SHA-256 is
`04ddbe3934185b0c484ca60579312aac6dc0d2412317cda58d8c518f8d214583`.
It checks the actual material link, native owners, density and neutral
JSON model round trip in both read modes. An unassigned control and an
invalid material claim measure the two additional read cases. Twelve
registry and direct calls preserve their caller's sink on refusal.

The typed reader source tree is `63af2e5e288a28834086415edf43eae3f195e91e`.
macOS Python 3.13 and 3.14 workers reproduce receipt SHA-256
`1542c7baa1f7f48c93e4baad0dcb5a3e541679bb48b2c2d89ba536f3bf8b940d`.
The [previous receipt](../measurements/2026/SdkAssignedPartMaterial01.json)
records the earlier source tree `7163bbf455aab4e5171676ce99798516d305fd1f`,
whose reader attached the physical evidence as a body attribute. The
typed reader adds zero native lifecycles, held-out cases and qualified
writer profiles.
