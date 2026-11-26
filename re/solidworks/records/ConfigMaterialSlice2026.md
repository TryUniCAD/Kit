# Ordinary SOLIDWORKS lightweight part material records

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-LW-MATERIAL` |
| Owner | PR #121 takeover team |
| Delivery | Separate main-target branch `codex/solidworks-config-material-owners` |
| Preparation base | `2759bcdb61c76c6b00fd467354cd85ace50f86bc`, accepted #188 |
| Prerequisites | [Standalone model headers](StandaloneHeaderSlice2026.md), [feature field actions](ConfigFieldActionsSlice2026.md) and [shared maps](ArchiveObjectMapSlice2026.md) |
| Exit | Both bounded native suffixes and original map identities, authored scalar and rejection cases in the queue, and current revision CI and review |

## Build and format rules

The version-19000 part lightweight method at model image address
`0x4c2309d0` reads the adjacent owners `f1418`, `f1420`, `f1588` and
`f938` in this order. The exact model image is SOLIDWORKS 2026 SP05.2
`34.5.2.0604`, SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
Its three tagged top-level positions and the nested density position
use schema one. The fourth position is embedded and has no class tag.

[Part section and field order](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/src/convert/adapters/solidworks/Archive/Bodies/Layouts/Config/ModelFields.py#L620-L647)
· [Exact-build runtime descriptors](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/solidworks/records/ConfigRuntimeDescriptors2026.json)

| Part field | Concrete typed scope | Preserved wire sequence |
| --- | --- | --- |
| `f1418` | `gcXhatch_c` | CString, two doubles and six signed words |
| `f1420` | `moMaterial_c` with concrete `moDensityParameter_c`, or null | Material object link, then the density parameter's shared node lightweight fields and `f48` link, `f58` double and `f68` byte |
| `f1588` | `uoModelData_c` | Null scene reference `f08`, then signed `f10` |
| `f938` | Embedded `moBodyVizProps_c` | Signed row counts `n08` and `n58`, both zero |

The exact material serializer at `0x4c224c60` selects its density
parameter object at current version. Density serializer `0x4c177fe0`
consumes `f68` outside archive condition `0x80`. A nonzero `f68`
selects a second double and native runtime normalization. The bounded
reader requires the ordinary zero condition, null inherited links,
and absent override. It refuses the alternate flag before the extra
double or later model fields. The density word remains a typed wire
value.

[Material and density native owners](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/solidworks/records/AssignedMaterialOwners2026.md#exact-native-model-and-serialization)

Model-data restore occupies `[0x4c3bb110,0x4c3bb2a3)`, SHA-256
`7e34331ceace0c5729e8876ed9bcac6477609d3436610855816a07a68cf6e930`.
The current native link may select a separate `uoScene` layout. This
reader admits an absent scene only. A wrong new child fails the role
check before its body. A mapped scene or other alias also fails. The
two embedded visual row counts each refuse a populated value before
reading rows.

[Model-data rules](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/solidworks/records/MaterialDisplayArchive2026.md#material-manager-and-model-data)

## Original part observations

The [source manifest](../measurements/2026/ConfigMaterialSource01.json)
binds the native parts, header and configuration streams, full group
and field hashes, typed content hashes, and every map allocation to
the exact aggregate source
`9f0ccb5389c121e750ca3b73f8e5d248b34d2e15`.
The pinned full Config reader was observed in memory against both
tracked originals, with its actual ModelHeader handoff intact.

| Owner | L1 boss interval and map | ConcaveOwned interval and map |
| --- | --- | --- |
| `f1418` | [2814, 2922), 49 to 51 | [1942, 2050), 46 to 48 |
| `f1420` | [2922, 2999), 51 to 55 | [2050, 2052), null, 48 to 48 |
| `f1588` | [2999, 3024), 55 to 57 | [2052, 2077), 48 to 50 |
| `f938` | [3024, 3032), 57 to 57 | [2077, 2085), 50 to 50 |

L1 allocates the material in slot 52 and its actual density parameter
in slot 54. The density occupies [2940, 2999), with `f58` at
[2990, 2998) and `f68` at [2998, 2999). It stores 1000.0 and no
override. Both model-data records have a null scene and `f10=0`.
The tagged hatch and model-data frames match between these two
controls while their allocated slots differ.

The new guarded process uses accepted `ReadPartStart` to verify the
actual physical lightweight interval and retain the real Config
root and independent header alias in slots 1–3. It seeds the measured
incoming counter, leaving unneeded intermediate slots unmaterialized.
The bounded reader compares every typed field and map entry against
the original measurements. Its completion state covers this suffix.
The rest of the model still has independent owners.

## Queue proof

The independent authored L1 contrast uses the real class descriptors
with fresh objects. Its 105-byte suffix retains changed text, distinct
signed and double fields, a new nested density owner and a signed
model-data word. The negative cases include wrong roles and archive
conditions, null or borrowed required owners, alternate density
state and names, both introduced and borrowed scene links, populated
visual counts, truncation and trailing data.

```sh
python -I -B re/tooling/sw2026/CheckCfgMat.py ladder
python -I -B re/tooling/sw2026/CheckCfgMat.py concave
```

[L1 queue case](../../../tests/Convert/Solidworks/Configuration/CfgMatTests.py)
· [ConcaveOwned queue case](../../../tests/Convert/Solidworks/Configuration/ImportMatTests.py)

The process guard denies filesystem, process and network access after
loading the bound files. Queue execution of this revision remains
pending. Model appearance `f78`, alternate density and scene states,
populated body visual properties, assigned material identity, full
configuration admission and native writing retain separate exits.

[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
