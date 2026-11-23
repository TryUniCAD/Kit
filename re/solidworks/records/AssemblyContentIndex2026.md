# Model-owned assembly document content index

Task `B04-SW2026-MATES-CONCENTRIC/source-content-index`, owner `/root`,
delivery [PR #121](https://github.com/TryUniCAD/Kit/pull/121). The scoped
constructor emits `SwDocContentMgr/SwDocContentMgrInfo` from an ordinary
flat assembly and its actual selected configuration, file bindings,
rigid transforms, direct mate list, and paired headers.
[Model emitter](../../tooling/sw2026/para/concentric/AssemblyContentIndex.py)
· [Guarded measurement](../measurements/2026/AssemblyContentIndex01.json)

| Record | Classification | Scope and construction rule |
| --- | --- | --- |
| `moBCModeInfo_c.f08,f28` | Authored location and name | The two actual header self-files agree. The logical `h10` is the owning model's title and physical `h18` is its explicitly supplied path. The unlocated state has an empty path. |
| Mode `f10,f18,f20` | Derived document clock | Alias the owning header creation seconds `f70`, update seconds `f48`, and unsigned update stamp `f40`. The generated headers follow their own authored chronology. |
| Mode `f30`, root `f38,fb0` | Derived inventory state | These blank, populated-root, and blank-root words come from whether the active configuration owns any actual component. The saved empty case contrasts all three. |
| Mode `f38,fb0,fc0` | Derived configuration selection | Build one configuration record using the actual current CMgr name and ID. That name also selects the review-mode configuration and indexes the empty parent name in this single base configuration. |
| Mode `ff4,ff8,ffc` | Derived units | Read the real length and system owners' `fb0` and the mass code at `moDensityUnits_c.fc4`. The eleven disclosed assemblies use millimetres, the MMGS system and grams. |
| Mode auxiliary tables and references | Neutral empty collections | The scoped configuration owns no density overrides, alternate parent, auxiliary selections, or external reference string array. Map base 1 and the shared writer compute allocation and every count. |
| Configuration `f10,f30` and state words | Ordinary active configuration vocabulary | `ACTIVE` and `0x80040180` agree in the saved empty, planar, and both unlocked and locked concentric designs. This single active configuration has no saved rebuild or update request. |
| `moBCNode_c` and `moBCPartNode_c` identities | Derived identity and direct occurrence role | The root is ID zero, with type 5 and the identity frame. Each actual direct part supplies its allocated ID and uses type 1. The direct part sentinel is `-1`. The native has-owner field `f10` distinguishes the root from its configured parts. |
| Occurrence order and display | Derived configuration ownership | Traverse CMgr's actual per-occurrence rows. Their detached reference IDs and names bind the true live model backlinks. This order can differ from Config-0's root occurrence list. Suppression comes from the actual configuration options. The scoped present components are visible, nonvirtual and carry no local attachments. |
| Part target, configuration and transform | Input identity and rigid placement | The occurrence's real `f3b0` target supplies its logical title and physical path. Its referenced configuration is `f3c0`. Its active rigid transform at `f360` is fully decoded and synthesized into the same matrix and translation fields. |
| Ordered mate descriptors | Derived selection and caption | Compose from the real MatesList nodes and their two ordered, active wrappers. The actual occurrence name supplies each bracketed endpoint. The display string, type and allocated mate node ID are emitted from the same live owners. |

The static verifier pins SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`.
`moBCModeInfo_c::syncHeaderTimeStamps` at `0x4b7426e0` reads the
header creation getter, copies the update time from header memory
`+0x48`, and calls the header update-stamp getter. It installs
the results at `+0x10`, `+0x18`, and `+0x20`. The selected
units, blank-mode predicates, node type and visibility also have
pinned getter evidence. The saved indexes span 420 to 2,268 bytes
and have next-map counters of 11 to 21.

All eleven complete content index streams reconstruct byte for byte
from six binary owner streams and the observed version marker. The
source index is opened for equality only after reconstruction.
The source cohort includes zero, one and two occurrences, nine direct
mate descriptors, alternative configuration traversal orders and
translated and rotated components. Removing each of the six source
owners causes a separate refusal. A process guard checks zero file
reads during projection.

Three neutral-only guarded workers compose the new index with the
existing modeled D01 parent. The two repeated builds retain every
stream in the earlier 24-stream parent and the complete child.
The independent relocated target changes the index length through
the actual location owners. The generated index is projected again
from its newly written model and matches byte for byte. The source
admission ledger still records unmodeled parent streams. The evidence
adds zero native launches and zero held-out qualifications.

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveAssemblyContentIndex.py \\
  --disclosures /absolute/path/to/Oracle121Takeover \\
  --model-module /absolute/path/to/sldmodu.dll \\
  --output /tmp/UnusedContentIndexReceipt.json
```
