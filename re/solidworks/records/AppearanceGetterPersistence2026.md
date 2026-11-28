# Material enumeration and the saved appearance manager

The controlled trial publishes the same installed stock appearance and
sets classic roughness once on the original material handle in each arm.
Arm A saves without enumerating materials. Arm B calls
`GetRenderMaterials2` once for the active state after publication and
before saving. Both arms start from the same generated input at the
same encoded self locator. Geometry and feature checks run before
publication. Native save snapshots are immutable before the fresh
read-only observations.
[Oracle observer](../../tooling/sw2026/para/concentric/ObserveChildAppearanceContrast.py)
[Source trial preparer](../../tooling/sw2026/para/concentric/PrepareChildAppearanceContrast.py)

SOLIDWORKS 2026 SP05.2 `34.5.2.0604` passes all six fresh processes
and 136 numeric checks with both controls healthy. Both native saves
return `(true, 0, 0)` and both cold opens return error and warning zero.
Each original setter receives
`0x1.41b2f769cf0e0p-2` (0.3141592653589793).
Its binary32 rounding widened back to binary64 is
`0x1.41b2f80000000p-2` (0.3141592741012573).

| Saved arm | Actual ordered Definition records | Allocator | Bytes and terminal map |
| --- | --- | --- | --- |
| A, zero enumerations | Slot 12 stock original, full binary64 roughness | `[5, 0]` | 1,623 and 13 |
| B, one enumeration | Slot 12 visual reconstruction, widened binary32 roughness. Slot 13 stock original, full binary64 roughness. | `[6, 0]` | 2,365 and 14 |

All three records use actual published material ID `[4, 0]`. The stock
row retains `f30=0` and an uppercase `Materials` locator segment.
The reconstructed row uses the stock packed color in `f30`,
projection sentinel `f4c=-1`, and a lowercase `materials` segment.
Both locator spellings refer to the same pinned installed asset in this
experiment. The three RealView owners retain the same binary32 roughness
in both arms. All corresponding typed appearance leaves of Config-0,
the selected CMgr configuration, and the part-self VisualStates attribute
agree between the arms. Six linked streams in each saved file replay
exactly through the shared typed reader and writer. Both fresh native
observations return the widened binary32 value without saving.

The result distinguishes the two actual live records. On the pinned
build the self-material path of `GetRenderMaterials2` reaches
`sldapiu` `0x42d40b10`. It creates the visual-property wrapper at
`0x42d40dab`, retains the original public ID, inserts the object through
the appearance manager at `0x42d40f2a`, then restores that ID on the
returned raw object at `0x42d40f39`. A native pre-save enumeration
therefore adds a live manager entry while keeping the same published ID.
The `sldmatu` visual projection and conversion at `0x3c424340` and
`0x3c485580` widen the RealView binary32 value for the reconstructed
record. Definition writes the original binary64 value in the original
record. The ordered manager stores before and after the getter support
the extra internal-key allocation. The archive does not serialize that
map key separately from the row's public ID.
[Earlier layout and restore evidence](ConcentricStockChildAppearanceCodec2026.md)
[Installed module fingerprints](../v2026/Manifest2026.json)

The first transport attempt returned `PrlJob_GetResult: Invalid
argument` before the leading control created a receipt. The trailing
control passed and no candidate phase ran. A separate new locator was
frozen for the complete successful retry. The accepted trial SHA-256 is
`787dca83f93df48b235591550657746595cff6e8688063da653a17c1f5f98866`.
The native result SHA-256 is
`d35d4686836513165f59bae69fa45878f1eb8f73a14ba64cc99fccaf61c33639`.
The typed audit SHA-256 is
`2131d839968094c7d919b4379b473166ad929863b5d5205485b60b93c1e3516a`.
This trial supplies source evidence for the stock asset and actual
getter path. The generalized asset, DSPBR and attachment writers
require their own field rules and prospective tests.
[Typed receipt](../measurements/2026/AppearanceGetterPersistence01.json)
[Audit reproducer](../../tooling/sw2026/para/concentric/AuditMaterialGetter.py)
