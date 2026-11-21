# Principal-plane boss revolve source lock

Five fresh SOLIDWORKS 2026 SP05.2 parts passed native authoring, rebuild
and fresh reopen. The two independent Top and Right inputs also passed
driving-angle edits. The original saves and authored specifications
were sealed before the writer implementation.
Both controls passed across twelve distinct SOLIDWORKS processes. The
lock predates the SDK Top and Right preparation extension and contains zero writer
outputs. [Source lock](../v2026/heldout/PrincipalRevolveSourceLock01.json)

| Item | Boundary |
| --- | --- |
| Task | B04-SW2026-REVOLVE-PRINCIPAL |
| Owner and native oracle custodian | PR #121 takeover |
| Delivery | [PR #121](https://github.com/TryUniCAD/Kit/pull/121) |
| Authoring revision | `954e5773df5088df4995701ea684f98ecb1dcac1` |
| Production source tree at lock | `f6830bfd53fc99747c91ca4a3cd7eead3915d6ee` |
| Oracle | SOLIDWORKS 2026 SP05.2, `34.5.2.0604`, COM `SldWorks.Application.34` |
| Guest lock receipt SHA-256 | `ac1a3c15db459409ab3a7aacf1281feba1c714bae8e6c8b8d7ae5d04930ab722` |
| Tracked LF lock receipt SHA-256 | `9396b94d1d503a0389c1db4ce7711125429265b271694bbe28a890b49059dc48` |
| Exit | Preserve the actual selected axis, support, direction, driving angle, tree and geometry through saved native rebuild and fresh reopen |

The disclosed controls comprise a Front full turn and a Top
partial-turn direction pair. The sealed inputs change the radius,
axial range, selected axis placement and angular end independently
on Top and Right. The guest-native specification file remains
under the private job directory. Only its digest, the source file
hashes and the phase receipt digests were carried back. The pinned
older Front full-turn control brackets the authoring and reopen
phases. [Existing native author](../../tooling/sw2026/AuthorRevolveSources.py)

The earlier SDK admission bound the profile to Front. The
shared principal-frame extension now checks the selected line
in the actual support frame and generates the model-space cache in
`moLineRef_w.fc8/fe0`. The disclosed Top pair and independently
authored Right case establish the two additional placements.
Freeze the writer and comparison before releasing either sealed case.
[Axis cache evidence](../../../Documentation/Gotchas/Conversion/Solidworks/Model/RevolveAxisCacheUsesModelCoordinates.md)

## Disclosed archive measurements

All four pinned native files reproduce the ten measured streams
through typed graphs. The pinned CLI projects the revolve owner in
each case and retains the unqualified research marker. The
unresolved counts are 48 for Front and 58 per Top or Right file.
[Pinned assets](../v2026/PrincipalRevolveDiscoveryManifest01.json) · [Archive and CLI receipt](../measurements/2026/PrincipalRevolveDisclosedArchives01.json)

The `moCompRefPlane_c.ff0.f00` field binds the actual datum.
Its `f100` codes are Front 3, Top 2 and Right 1. The profile's
`pd_ff0` uses the same datum frame. In model metres, the
ordered local point `(u, v)` maps to `(u, v, 0)` on Front,
`(u, 0, -v)` on Top and `(0, v, -u)` on Right. The selected
construction handle still identifies the actual profile line.

| Owner | Classification | Disclosed evidence |
| --- | --- | --- |
| `moLineRef_w.fc8` | Derived model-space first endpoint | Front `(0.002, -0.013, 0)`, Top `(0.004, 0, 0.016)`, Right `(0, -0.0219, -0.0093)` |
| `moLineRef_w.fe0` | Derived unit vector of the ordered line | Front and Right `(0, 1, 0)`, Top `(0, 0, -1)` |
| `moLineRef_w.fb8` | Derived projection of the endpoint difference onto the unit vector | Front `0.037`, Top `0.039`, Right `0.0421` metres |
| `moLineRef_w.fb0` | Local line parameter origin | Zero on all four sources |
| `moLineRef_w.f68` | Volatile cache validity | One in all four native saves. The fresh wrapper uses the previously measured cold value zero |
| `moRevolution_c.f824` and D1 | Explicit sweep sense and positive angle | The Top contrast changes reverse without changing the cache point, direction or span |

The pinned SP05.2 resolver slice at virtual address `0x4c316200`
in `sldmodu.dll` was inspected through REA and Ghidra. The
2,048-byte slice has SHA-256
`293379a3537f5073e13b7b5bd6fbd2c1ad6780bcbde45c97c90be1cbfc70d3dd`.
The private REA receipt has SHA-256
`9c371d8c7cc5bbe734bb55b79e4341518271b811f9097e413a83056933036190`
and ID `ev_6a40f9aeef14de6076e9654e78dd0f5246a154e56e1f5c06a8f3737512067b29`.
The bounded result preserves the prior loader context. The archive
and native measurements establish the field ownership across these
planes. [Local resolver and cache update](OrdinaryRevolvedBossLoad2026.md)

## Generated preparation

Four guarded workers build the disclosed shapes from authored
neutral documents with no external access. Their path and named
stream preparations yield identical files. All 40 generated
load-critical streams replay exactly. The strict SDK reads each
generated part's closed solid, actual datum, selected line and D1.
Four more guarded workers refuse translated and rotated supports,
an unrelated axis origin and a direction perpendicular to the
selected line.
[Guarded builder](../../tooling/sw2026/revolve/PrincipalWriter/BuildPrincipalRevolves.py) · [Preparation receipt](../measurements/2026/SdkPrincipalRevolvePreparation01.json)

All four disclosed generated parts open with one solid before
explicit rebuild and zero opening errors or warnings. Their live
D1 edits rebuild, save and reopen in fresh processes. All 19
reported top-level tree rows and the selected axis match the
corresponding native source in all three lifecycle observations.
Body count matches exactly. All 72 mass, volume, area and
centre-of-mass values match to six significant figures, with a
`10^-12` metre zero threshold for centre-of-mass components.
Both controls pass across ten distinct processes. These
disclosed cases supply preparation evidence. The two held-out
sources were still sealed during this batch.
[Native comparison](../measurements/2026/SdkPrincipalRevolveNative01.json) · [Comparison tool](../../tooling/sw2026/revolve/PrincipalWriter/ComparePrincipalRevolves.py)

## Independent native evaluation

Both pre-writer locked sources matched their generated Top and
Right candidates through native open, rebuild, D1 edit, save
and fresh reopen. All ten process births were distinct and
both controls passed. Each pair retained all 25 recursive
feature rows, the actual solid label, four sketch relations,
the selected axis and signed geometry. The 36 mass-property
values match to six significant figures under the preregistered
near-zero centre rule. Eight strict SDK process reads reproduce
80 typed streams and retain the actual D1 and axis owners.

Both candidate hashes precede the first native open of the
originals. The corrected Windows observer recovered from a
portable audit-hook error using these same candidates and the
same production SDK tree. The frozen reader reported the cold
`Body 1` placeholder. The later creator binding recovers
`OrdinaryBossRevolve`, matching the native and strict saved label.
Full original-source preparation and original FCStd conversions
remain open.
[Evaluation receipt](../measurements/2026/SdkPrincipalRevolveHeldoutNative01.json) · [Generation pin](../v2026/heldout/PrincipalRevolveGenerationPin01.json) · [Method and recovery](PrincipalRevolveHeldoutProtocol2026.md)

## Registry and cross-host measurements

The normal SDK registry and direct adapter reproduce both exact
candidate hashes on Windows with the original authored intent,
final paths and explicit writing epoch. The two positive
workers replay all 20 measured streams and recover both derived
body labels. Five other workers refuse unsupported requests.
All seven record zero guarded external access attempts.
[Public writer receipt](../measurements/2026/SdkPrincipalRevolvePublicWriter01.json)

Both macOS builds from the same intent preserve nine of the ten
logical stream hashes. The remaining Config-0 bytes represent
eight standard-view matrix coefficients in `moView_c.f368.f08`.
The affected Left and Right rows use `m0` and `m8`. The
affected Top and Bottom rows use `m4` and `m8`. The Windows
coefficient is `-0x1.ffffffffffffep-49`. The macOS coefficient is
`-0x1.0000000000000p-48`. The binary64 variation follows the
previously observed platform cosine difference in the shared
quaternion calculation. Both strict SDK readbacks retain the
signed axis, live D1 and closed solids.
[Exact host comparison](../measurements/2026/PrincipalRevolveHostViewParity01.json) · [Standard-view construction](StandardViewsConstruction2026.md) · [Previously isolated trigonometric variance](PerpendicularMateBlindMethod2026.md)

Both macOS-generated parts opened with a solid before explicit
rebuild and zero opening errors or warnings. The existing D1
drivers edited, rebuilt, saved and reopened in fresh processes.
All 36 paired mass-property values match the locked sources.
Both controls passed across six processes. This host-portability
comparison reuses the already evaluated source intents.
[macOS-generated native lifecycle](../measurements/2026/SdkPrincipalRevolveMacNative01.json)

## Oracle procedure

The preparation helper must run in the same Windows guest as the
native author. Set the tool paths to the pinned copies on the Mac
share and choose an unused private guest directory. The preparation
prints the exact native job locator and digests.

```sh
prlctl exec 'Windows 11' --current-user "$guest_python" -B "$guest_prepare" \
  --workspace "$private_workspace" --checkout "$guest_checkout" \
  --control "$guest_control" --source-revision "$source_revision"
prlctl exec 'Windows 11' --current-user "$guest_python" -B "$guest_author" "$guest_job"
```

The first capture used job SHA-256
`2a5528e57cbf9f65cfa4aea68626fe0a6bb2052f28c154867230b571d663056c`
and private specification SHA-256
`13be8abb8186c7a876637ea27e93c0b35083c0ea34cbf4b052d3b8988a81e457`.
[Preparation tool](../../tooling/sw2026/revolve/LockedEvaluation/PreparePrincipalRevolveLock.py)
