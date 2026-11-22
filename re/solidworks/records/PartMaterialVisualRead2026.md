# Ordinary SOLIDWORKS part material visual prefix

| Delivery item | Scope |
| --- | --- |
| Related task | `B04-SW2026-CONFIG-LW-MATERIAL`, an archive prerequisite for `B04-SW2026-NAMED-MATERIAL` |
| Owner | PR #121 takeover team |
| Delivery | Separate main-target branch `codex/solidworks-part-visual-member` |
| Preparation base | `d5a72e06a1402d7b9f64c1a4c35f84844f42416b` |
| Prerequisites | [Physical header handoff](ConfigHeaderLinkSlice2026.md) and the existing lightweight node and shared map codecs |
| Exit | Exact guarded prefix replay, tagged role and selector refusals, tracked queue control and contrast, current revision review and queue evidence |

## Physical ownership

The confirmed wire scope is the ordinary format-4, version-19000 part
lightweight prefix through concrete schema-one `moVisualProperties_c`.
`ReadPartStart` checks the physical ModelHeader and installs its actual
entries in the part map. The reader consumes signed `fb0`, unsigned
`fb4`, and the shared `moConcept_c.SerializeLWData` base. The latter
reaches `moNode_c.SerializeLWData/f18` and then its own `f78`. The
callback checks every newly declared tagged body at its actual field
path and depth. Both tagged children must be newly mapped.

The visual owner selects material properties at `f20` and the
physically based rendering record through `has88`. The material
record's own `f20` is its stored IdName CString. In the measured lanes,
`has80` chooses a primary texture with thirteen f64 values and its
typed trailing fields. `has90` selects the renderer restore record.
Only the observed combinations of `f70`, `has80` and the required
renderer and PBR states are admitted. A secondary texture, populated
material user properties or a different selector combination refuses.
Material, renderer and texture fields retain their wire meaning.
Portable appearance and catalog semantics are separate.

Exact SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` authority includes the
part lightweight routine at `0x4c2309d0` in `sldmodu.dll`, the visual
restore caller at `0x3c922b80` in `sldmfcu.dll`, and its PBR helper
`0x3c779740`. The aggregate records bind the module hashes, relevant
function ranges and assignment lineage.
[Part lightweight section](ConfigMaterialSlice2026.md) ·
[Material and renderer field authority](https://github.com/TryUniCAD/Kit/blob/c181cc057089eb1dbf6149f12158c5d846ce1c3a/re/solidworks/records/MaterialDisplayArchive2026.md) ·
[Assignment ownership contrast](https://github.com/TryUniCAD/Kit/blob/c181cc057089eb1dbf6149f12158c5d846ce1c3a/re/solidworks/records/AssignedMaterialOwners2026.md)

## Process evidence

The [receipt](../measurements/2026/PartMaterialVisualRead01.json)
binds seven assigned saves and one unassigned control to their prior
native observation receipts and the current reader sources. Each fresh
worker parses the original CFB bytes supplied on stdin, retains the
actual ModelHeader entries and advances the native map from 4 to 8.
Replay of each consumed prefix matches every byte. The workers record
zero filesystem, process or network accesses while interpreting the
provided bytes. Nine guarded contrasts refuse wrong or borrowed bodies,
missing owners, alternate or populated visual lanes, section truncation,
and bad physical framing. No captured field values enter the production
reader or any writer.

```sh
python3.14 -I -B re/tooling/sw2026/materials/ProvePartMaterialVisual.py \
  --source /path/to/SdkNamedMaterial01 \
  --output /tmp/PartMaterialVisualRead01.json
```

The command uses the recorded aggregate evidence blobs at
`c181cc057089eb1dbf6149f12158c5d846ce1c3a` and known disclosed inputs.
The tracked [queue process cases](../../../tests/Convert/Solidworks/Configuration/MaterialVisual/PartVisualTests.py)
use the same worker with only files on main. L1 consumes physical
prefix `[18, 925)`, with `f78` in slot 7 at `[82, 925)`.
ConcaveOwned reaches the distinct selector refusal. Hosted execution of
the added queue cases is pending.

The disclosed unassigned control stores the label `Steel` while its
active configuration has density sentinel `-1`. Physical assignment
still needs a linked `Contents/CMgr` active row, complete
`Contents/Config-0` traversal to the physical density and atom
owners, and corroboration by `MATERIALTREE`. The prefix does not
admit a complete configuration or any portable material assignment.
These disclosed cases receive zero held-out or native-write credit.
