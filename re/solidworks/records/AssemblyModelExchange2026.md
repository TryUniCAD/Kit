# Ordinary assembly model exchange database

Task `B04-SW2026-MATES-CONCENTRIC/model-exchange` in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). This composition covers one active configuration, three ordinary standard datums, an empty selection folder and either an empty mate group or the measured direct concentric mate profile. The format authority is SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`, version `19000`. [Database store](UnqliteExchangeStore2026.md) · [Configuration database](ConfigHeaderExchange2026.md) · [Endpoint owner](ExchangeMateEndpoints2026.md)

| Ordered record | Classification and ownership |
| --- | --- |
| `moConfigurationMgr_c` | The actual manager supplies persistent ID and `f29c` update stamp. The stored document path comes from `Header2.moHeader_c.f38.shared.h18` when present. The ordinary profile writes false hidden and suppressed and an empty override array. |
| `moSelectionSetFolder_c` | The resolved node supplies its allocated ID, name and update stamp. Its actual `f3c0` selection list has zero rows. The repeated class, visibility, suppression and update entries use the shared desktop object framing. |
| Three `moRefPlane_c` records | Each actual resolved node supplies ID, name, mode and stamp. `moDefaultRefPlnData_c` carries the plane point, normal and rigid transform. The converter transposes its matrix, retains signed zeros and includes the actual transform translation. |
| `moMateGroup_c` | The ordered `Config-0-MatesList` extends its registered group. Nonempty ordinary groups carry `Mate0` and `NumberMates` for the measured single member. The group contributes its name and update stamp. |
| `TOC` | The repeated `object` entries join the actual allocated keys for the selection folder, mate group and three datums. The actual active manager configuration supplies name and ID. The disclosed source ordering varies across independent saves and survives paired edits. Fresh output orders the datum references by their generated resolved sequence. |
| `uiAssemblyDoc_c` | The concrete document class and desktop document flags follow the same measured ordinary defaults as the standalone part transport. |

The `moFeature_c::to_msgpack` dispatch at `0x4bb536a5` calls the actual datum's visibility virtual before writing the second `hidden` entry. For `moRefPlane_c`, cell `0x4d170b48` resolves to `moRefGeom_c::isVisible` at `0x4c2ceca0`. The standard datum mode writes `f6dc=5`; its low two bits equal one and return zero visibility. The profiled graph permits both measured archive node flags with this mode. The compositor retains the inherited numeric zero separately from the Boolean hidden value. The [receipt](../measurements/2026/D01ModelExchange01.json) pins the exact module and four native windows.

The concentric record supplies `Aligment` from the actual `f3b4` value and `LockRotate` from `f4b8`. It emits two ordered `Ref` records from the same child graph used by the native mate archive. The direct endpoint title and actual selected face attribute provide the text fields. The mate owns the description, persistent ID and update stamp. [Concentric archive](ConcentricMateArchive2026.md) · [Face attribute rule](ExchangeMateEndpoints2026.md)

The disclosed comparisons reconstruct 95 live records byte for byte across twelve assemblies. Eleven stores match all eight logical records, including four empty groups, six D01 to D03 source and edited states and the renamed native control. The A1 planar case matches all seven system records and uses its independent planar endpoint comparison for the eighth. Source comparison restores the observed record identities and `TOC` order. The shared physical writer constructs fresh empty space from the derived records.

Two isolated processes construct the full 34-stream D01 research parent from stdin. The model record keys are derived separately for each role from the neutral package and authored database creation event. All other 33 parent streams and the complete child reproduce the prior bytes. The decoded databases join the same active configuration and confirm separate key identities. An existing model exchange stream rejects a second publication. Runtime external accesses are zero. Nine original D01 members remain outside the composed inventory. [Proof](../../tooling/sw2026/para/concentric/ProveD01ModelExchange.py) · [Numeric receipt](../measurements/2026/D01ModelExchange01.json)

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01ModelExchange.py \
  --disclosures /absolute/path/to/Oracle121Takeover \
  --model-module /absolute/path/to/sldmodu.dll \
  --output /tmp/UnusedD01ModelExchange.json
```

Native lifecycle verification of the new parent, held-out qualification, other mate families and public publication remain open.
