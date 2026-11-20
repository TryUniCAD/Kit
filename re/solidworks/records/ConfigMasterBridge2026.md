# SOLIDWORKS 2026 direct configuration master

| Delivery item | Scope |
| --- | --- |
| Task | B04-SW2026-CONFIG-MASTER |
| Owner | PR #121 takeover team |
| Delivery | Main-target branch codex/solidworks-config-direct-owner |
| Dependencies | Accepted part ModelHeader binding, shared feature layout and concrete virtual dispatch |
| Exit | Exact present and absent native intervals, typed child and inherited map, authored contrasts, current-revision queue and review |

The model stores signed f1014 as a distinct scalar. Zero leaves f1018
absent. A nonzero value enters the inherited feature body of the concrete
`moSheetMetalMaster_c` without a separate archive tag. The four virtual
targets select its concept lightweight and resolved fields and its
feature XML path. The record has its own field scope and no map slot.
The final signed n370 owns the per-body list. This bounded reader
accepts an empty list and absent feature links. Other variants require
their own ownership and source evidence.

| Saved part | Selector and body span | Selector | Body bytes | Map before to after |
| --- | --- | ---: | ---: | ---: |
| RectangleProperties | [25099, 25103) | 0 | 0 | 105 to 105 |
| CircularProperties | [25320, 25473) | 1 | 149 | 119 to 119 |
| CircleRadiusBoss open-save | [24214, 24367) | 1 | 149 | 118 to 118 |

The pinned full source traversal used aggregate revision
`9e0a4b85dd21cdfb7feb50eda94593ef9e9b01f9` for the physical feature grammar.
The earlier version-specific DLL analysis binds the concrete serializer
and its callback cells. The model header and part prefix identify the
real caller. The process checks use the measured initial counters and
retain the original root and header identities. CircularProperties and
CircleRadiusBoss differ in f28c and other stored feature words.
[Static serializer evidence](https://github.com/TryUniCAD/Kit/blob/9e0a4b85dd21cdfb7feb50eda94593ef9e9b01f9/re/solidworks/records/SmmMasterArchive2026.json)

The independent frames use selectors -7 and 41, different Unicode
lengths, a present inherited field and a separate embedded width. Nine
refusals cover version, detached owner, missing or appended bytes, an
incorrect outer tag, a borrowed owner and alternate counts. Three fresh
processes check the saved controls and authored cases with zero guarded
external accesses. The saved documents are disclosed controls. This
scope receives zero held-out or generated-file credit.
[Guarded evidence](../measurements/2026/ConfigMasterBridge01.json)

```sh
python -I -B re/tooling/sw2026/CheckCfgMaster.py rectangle
python -I -B re/tooling/sw2026/CheckCfgMaster.py circular
python -I -B re/tooling/sw2026/CheckCfgMaster.py circle-save
```
