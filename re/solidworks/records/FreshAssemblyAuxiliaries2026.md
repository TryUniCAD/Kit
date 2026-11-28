# Fresh assembly auxiliary stream defaults

Task `B04-SW2026-MATES-CONCENTRIC/source-fresh-auxiliaries`,
delivery [PR #121](https://github.com/TryUniCAD/Kit/pull/121). These
fields apply to the scoped fresh flat assembly with no transferred
attachments, embedded objects, open-time history, motion loads or
schedules. Its default motion study uses the measured English label.
[Guarded evidence](../measurements/2026/FreshAssemblyAuxiliaries01.json)

| Stream | Classification | Construction |
| --- | --- | --- |
| `docProps/OpenTime.xml` | Constructor defaults with typed XML framing | Serialize the normal and lightweight count as zero and both totals as `-1`. Emit the native field names, empty child namespaces, UTF-8 declaration and CRLFs. |
| `Contents/Config-0-Attachment` | Neutral empty attachment index | Encode the zero row count with the same short archive count codec used by the model. |
| `Contents/OleItems`, `OleItemInformation/OLE_Item_Data` | Empty embedded-object metadata | Both streams contain one zero 32-bit word when this scoped model carries no embedded objects. |
| `ThirdPty/CMMotionLoadMapU` | Default study mapping | Emit one row. Store the UTF-16LE study label with its UTF-16 code-unit length and the ASCII load member name with its byte length. Every length and the slot name follow the empty first study. |
| `ThirdPty/CM_MOTION_LOAD_1`, `ThirdPty/SWA_Schedules` | Empty linked load and schedule members | The default study's load member and the independently named schedule member have zero records and zero bytes. |

The pinned SOLIDWORKS 2026 SP05.2 MFC DLL verifies the
`suFileOpenTime` constructor at `0x3c7c93f0`. Its count and total
pairs at `+0x10,+0x14` and `+0x18,+0x1c` initialize to
`0,-1`. Native property storage resolves the corresponding total
labels and the `OpenTime.xml` member. The exact module also contains
the attachment suffix and the scoped OLE and motion storage labels.
The selected defaults agree in eleven different saved assemblies,
including the paired edits, a planar mate group and an empty
assembly. The emitted metadata matches all 77 stream comparisons.

Two guarded stdin-only workers add the seven members to the existing
25-stream neutral D01 writer. Their whole parents match, every prior
stream and the complete child reproduce exactly, and a second
publication over the same scope refuses. Eleven original D01 stream
members still lack complete construction or admission evidence.
The timing and storage comparisons add zero native launches or
held-out qualifications.

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveFreshAssemblyAuxiliaries.py \\
  --disclosures /absolute/path/to/Oracle121Takeover \\
  --mfc-module /absolute/path/to/SLDMFCU.dll \\
  --output /tmp/UnusedFreshAssemblyAuxiliaries.json
```
