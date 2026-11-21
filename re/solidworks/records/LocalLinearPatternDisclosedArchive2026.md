# Disclosed linear-pattern archive intake on SOLIDWORKS 2026

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`, owner `assembly_frontier` for this intake, delivery PR #121. The exact codec revision is `5664d55335d9af2403f60ffe1f59ee0e8aba89bc`. The published D01X/D02Y source lock at `d00e45fbc24b8da87c02999c914aa45dbfaa2f62` has SHA-256 `8239fc92779aadd6a0116ad2df9e7969568394a301e1ed11aa44fc3875ac0426`. All six native part hashes and the records of 14 distinct source/control processes were rechecked. Both controls passed on build 34.5.2.0604. This is a disclosed source intake. Separate held-out originals stay in guest custody. [Existing layout and ownership](LocalLinearPatternOwnership2026.md) · [Audit receipt](../measurements/2026/LocalLinearPatternDisclosedArchive01.json)

## Exact archive coverage

Each format-4/19000 part contains 40 streams. The serializers replay 15 planned streams in each part without a trailing byte. The combined audit records 90 exact replays, including 84 zero-raw independent streams and six exact linked Resolved streams through the existing research codec. Production Config-0 and Definition independently re-emit exactly. The linked research Resolved codec has no missing or provisional schemas for these six snapshots. Each Resolved decode preserves eight 8-byte display caches as raw operations under `dm.FUN_4bd03960.data`, six for `moDisplayDistanceDim_c` and two for `moDisplayDim_c`. The corresponding encode has the same eight operations. These six replays still carry that raw-cache obligation.

Production `ReadNativeLink` reads the configuration and manager, then accepts 21 of 22 ordered Resolved roots. The first unsupported root is schema-one `moLPattern_c`, persistent feature ID 47. Its tag and body start at offsets 18,147 and 18,165 in both originals, and 18,357 and 18,375 in both edit variants of both cases. The decoded research object ends at 28,875 or 29,085 respectively. D01X links the actual Config map counter 112 to final Resolved counter 427. D02Y links 113 to 428. The counters are unchanged by the two separate edits in each lineage.

The default public reader still exposes one cached body and a generic `NativeFeatureDefinition`. Its heuristic `selection_kind=edge` disagrees with the actual saved plane direction in both cases. The typed source evidence below gives the correct owner.

## Saved feature and reference owners

| Role | Observed exact owner |
| --- | --- |
| Pattern seed | `moLPattern_c.f988` contains one aliased `moICE_c` root, feature 40 `SeedBoss`. The seed identity matches the native definition. The other seed list `f9d8` is empty and skip array `f820` is null in all six saves. |
| Active direction | `f1288` is a `moLineRef_w`; its `f58` points to `moCompRefPlane_c` whose unit component owns the actual Config part root. The plane ID comes from that wrapper's `ff0.f00`. Its creation field `ff0.f08` equals the selected plane's first event in both headers. The direction is not a new standalone axis. |
| D01X direction | Wrapper `f100=1` binds Right Plane ID 4. Line `fe0=(1,0,0)` and `f1298=0` produce +X. |
| D02Y direction | Wrapper `f100=2` binds Top Plane ID 3. Line `fe0=(0,1,0)` and `f1298=1` produce −Y. |
| Active count | `f1258 → moDisplayDim_c → moFeatureDimHandle_c → moNumberDim_c → moIntegerParameter_c`, D1, persistent dimension ID 41. Parameter `f58` supplies the integer, and a distinct f64 display cache carries the same numeric value. |
| Active spacing | `f1260 → moDisplayDistanceDim_c → moFeatureDimHandle_c → ParallelPlaneDistanceDim_c → moLengthParameter_c`, D3, persistent dimension ID 42. Parameter `f58` and the display cache equal the native API metre value. |
| Inactive displays | D2, D4, D5 and D6 still own distinct typed vertices. D2 stores integer one with display cache zero. The three other inactive drivers and caches store zero. The second direction wrapper `f1290` is null. |
| Selected stock | `f544=1` and one `f548` wrapper select immediate atom 102, the seed's joined result. Its `f18/f1c` duplicate that atom, `f110` walks 102 then 101, and `f108` identifies base PlateBoss feature 32. The selected wrapper retains a separate face and zero `f100/f104` remap words. The seed feature identity 40 remains independently owned. |
| Atom evolution | PlateBoss 32 creates 101. SeedBoss 40 consumes the same managed 101 and produces 102. LinearPattern 47 consumes the same managed 102 and produces the only live atom 103. All three feature output objects alias Config-0 atom-manager membership. |

The count/spacing pairs (count, mm) are D01X `(3,27.183)`, `(3,31.427)`, `(4,27.183)` and D02Y `(4,25.163)`, `(4,29.173)`, `(5,25.163)`. Each separate edit changes only its corresponding driver value and the matching display cache among all six drivers. The numeric receipt retains the native body, volume, area and centre observations. Names, timestamps, stored display cache bytes and pattern-state leaves here are source evidence. The audit emits no CAD files or writer data.

The next decoder task is to move the ordinary current `moLPattern_c` inheritance path and the distinct integer count driver into the shared typed grammar, preserving the linked scope wrapper and typed 8-byte display arrays. The existing research definitions are the exact layout baseline. Portability of other pattern modes, the actual initial archive construction state and native writer acceptance remain open. No writer work or fresh native process took place in this intake.

```sh
PATTERN_AUDIT="$(mktemp -d)/Receipt.json"
python3.14 -I -B re/tooling/sw2026/linear_pattern/AuditLinearPatternArchive.py \
  --packet /absolute/path/to/LinearPatternSourcePacket03 --output "$PATTERN_AUDIT"
```

The current internal SDK codec has since passed the six complete linked Config/Resolved comparisons with typed display cells. The revision-bound successor keeps this original source-intake result and records the remaining public projection and construction limits. [Typed archive progression](LocalLinearPatternTypedArchive2026.md)
