# Read the ordinary SOLIDWORKS 2026 planar mate group

Task `B04-SW2026-MATES-PLANAR/saved-group-read`, owner `assembly_frontier`, delivery PR #121. The typed SDK reader projects the existing flat parent group and its ordered mate references. This step follows the prior child-label bridge at `1f2130d9fcf4f3fa4abdf8b0af0a6c4c018cdb58`. [Prior source bridge](SdkPlanarSourceLabelBridge2026.md) · [Evidence](../measurements/2026/SdkPlanarMateGroupRead01.json)

## Native ownership

The pinned 34.5.2.0604 `uiModelDoc_c::saveMateList` copies the actual group's runtime `+0x60` children and stores their ordered object list after the resolved archive count. The paired `moModel_c::loadMateList` selects the first group, then appends each decoded mate at `0x4b5881b9`. The missing-group creation branch remains outside the SDK projection. The stored group's own `f60` is empty because its children are loaded through the separate list. [Pinned save and load](AssemblyMatesList2026.md) · [Registration](CoincidentMatePublication2026.md)

Both original source records independently report a root `MateGroup` named `Mates` and the following immediate children in the same order as their separate lists. The group is concrete schema one at resolved ordinal 15 in both cases. The portable group retains the actual name, root definition ID, hierarchy, neutral mate IDs and provenance to bytes `[5101,5295)` of `Contents/Config-0-ResolvedFeatures`. The members retain their own separate archive provenance. [Original custody](../v2026/heldout/AssemblyPlanarMateSourceLock01.json)

| Prior disclosure | Group feature ID / map slot | MatesList map base / end | Ordered member feature IDs and names | MatesList bytes |
| --- | --- | --- | --- | ---: |
| A20 | 11 / 166 | 168 / 226 | 26 Coincident1, 28 Distance1 | 7,831 |
| A21 | 11 / 170 | 172 / 232 | 27 Parallel1, 29 Distance1 | 8,279 |

The shared group reader requires one concrete root object at its actual inherited map slot, with no alternate typed group or enclosing resolved feature child list. It requires empty inline `f60`, empty discarded manager records and `f4e8`, and absent conditional `f4f8`. The stored `hidden`, `has_list68` and `f35c` words are zero. The permitted group and member `f0c` pairs are `0 / 0x100` for a saved graph and `1 / 1` for the measured generated planar graph. Every projected mate must belong to the same root, have the decoded list position and retain the exact native member provenance. [Group projection](../../../src/convert/adapters/solidworks/Core/TypedMates/ReadMateGroup.py) · [Public entry](../../../src/convert/adapters/solidworks/Core/TypedMates/ReadPublicMates.py)

## Guarded comparison

The proof runs nine before-and-after strict SDK comparisons and ten refusal workers in 28 fresh host processes. It uses default and metadata-only reads for the two sources, and exact generated and saved planar registry pairs, a native-saved perpendicular pair, the unsupported generated perpendicular precursor, and the existing D01 concentric control. Each worker restricts CAD file reads to its declared parent and child, permits the hash-bound SDK root layout rule file for the existing cylinder reader, prohibits process and network operations, and checks that no CAD modules were loaded. The only differences on the admitted new profiles are the mate group and its derived document semantic seal. The complete D01 document and the generated perpendicular refusal agree with the base. The eight admitted current reads compare both linked streams in memory for 16 exact byte comparisons. [Process evidence](../measurements/2026/SdkPlanarMateGroupRead01.json)

The probe also injects independent in-memory ownership errors at the same normal typed entry. Extra or detached groups, crossed slots, nested group references, inline members, unexpected group ID records, crossed update states, foreign mate owners, crossed member provenance, and reordered rules fail typed admission. The locked files stay unchanged.

```sh
python3.14 -I -B re/tooling/sw2026/planar_registry/ProvePlanarMateGroup.py \
  --disclosed /absolute/path/to/Oracle121Takeover \
  --output /tmp/KitPlanarMateGroupRead01.json
```

## Writer boundary

Both originals still refuse ordinary write preparation at `CheckAsmRoot` with `assembly root contains unprojected model content`. Their retained 25 and 26 root timeline rows, `sldasm.native_record_unresolved` diagnostic and other source-owned domains require lossless normalisation before reassembly. Invoking the separate writer group gate on these read graphs advances to `mate group has unprojected extensions` because the group retains native provenance. This provenance must remain available in any source-preserving translation. The existing generator constructs a new group from the authored name and requires that its neutral IDs match every admitted rule in explicit order, with all mates, entities and parameters consumed. Writer eligibility and emitting code are unchanged. A20 and A21 are the previously evaluated cohort. This stage earns zero new held-out credit and starts zero native processes. [Root guard](../../../src/convert/adapters/solidworks/Core/AssemblyPreparation/Model/CheckAsmRoot.py) · [Group guard](../../../src/convert/adapters/solidworks/Core/AssemblyPreparation/Model/ReadAsmGroup.py) · [Membership guard](../../../src/convert/adapters/solidworks/Core/AssemblyPreparation/Mates/ReadAsmRules.py) · [Neutral generator](../../../src/convert/adapters/solidworks/Archive/Construction/AssemblyGroups/MakePlanarGroup.py)
