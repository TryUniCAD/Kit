# Transfer the disclosed concentric parent lights

Task `B04-SW2026-MATES-CONCENTRIC/parent-lights`, delivery PR #121. The bounded transfer preserves typed ambient and directional lighting through the shared assembly constructor and the normal metadata reader. The disclosed D01 scene and a separate authored light change have host and native evidence. Whole-source admission remains pending. [Process receipt](../measurements/2026/ConcentricParentLights01.json) · [Native receipt](../measurements/2026/ConcentricParentLightsNative01.json) · [Host proof](../../tooling/sw2026/para/concentric/ProveConcentricParentLights.py)

## Source and generated ownership

The actual selected `Config-0.moAssembly_c.f1e0` aliases the unique resolved `moEnvFolder_c`. Its counted `f60` rows contain one ambient light and three directional lights. Each member has one actual map entry and no separate resolved root. The three pinned source parents agree on all values returned by `ReadLightInput` after excluding creation clocks. The independently generated radial parent acquires the same four light intents when SOLIDWORKS saves it. [Earlier root audit](ConcentricParentRootAudit2026.md) · [Light owner fields](ThroughAllSystemMembers2026.md)

| Disclosed state | Environment ID | Ordered light IDs |
| --- | ---: | --- |
| D01 original and edit | 7 | 12, 13, 14, 15 |
| Native-saved radial parent | 8 | 20, 21, 22, 23 |
| New host-generated comparison | 8 | 17, 18, 19, 20 |

The writer consumes ordered `LightInput` values through `AssemblySysIn.LightValues`. The existing shared allocator assigns each light a new ID. Fresh feature creation instants come from the requested writer epoch and order. The source record retains its original clocks and IDs as evidence. The helper allocates the actual child objects under the environment through `MakeLightMut` and saves the typed nested list. Empty inputs keep their existing assembly path. [Typed system constructor](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/System/MakeAsmSysMut.py)

The ordinary assembly metadata reader starts from the separate `KeyWords` index. The native D01 index stores one flat `Feature` row for each actual light ID, with types `Ambient` and `Directional`. Flat and nested constructors index their common actual environment members through the same helper and retain the existing lexical sort rule. The helper requires the exact environment root, actual member parent, supported member class and distinct combined feature IDs. The member entries remain nested in the binary graph. [Keyword owner helper](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/Xml/AsmKeyNodes.py)

## Offline process evidence

The exact source closure starts at `a794b0b3adfbf619ad00bd177203eefddda571d5` with six changed SDK paths and the proof tool. The original and edited D01 and saved radial parents retain their immutable file and full SDK model digests. Both independent from-neutral builds produce the same parent and child bytes with zero guarded file, process or network attempts. The three linked parent streams reread and re-emit exactly.

The normal reader recovers all four generated light names, roles and allocated IDs. The resulting 22 feature rows consist of the prior 18 rows plus the four real lights. Config-0 grows from 22,563 to 23,839 bytes. A separate typed edit that lengthens one light label grows it to 23,877 bytes. The source-only metadata and the original D01 model remain in their separate evidence. No serialized source fields enter the generator.

The two prior flat fixtures and two prior nested fixtures retain their complete prior bytes and exact guarded receipts. Eight workers compare eleven parent/child or nested definition file pairs. Twelve refusal cases cover invalid scene input, name collisions, unexpected classes, source status, list state and duplicate or foreign publication owners.

## Native parent scene and persistence

The candidate changes one parent directional light's label, colour, diffuse
coefficient and specular coefficient. The child scene and independent
assembly, mate and depth predictions retain their established inputs. Two
guarded constructions match with zero runtime access. A same-locator empty
scene comparison records eight affected logical streams, including actual
light ownership, persistent ID allocation and the public Keyword index.

Four fresh SOLIDWORKS `34.5.2.0604` processes finish the two controls,
generated edit and save, and fresh reopen with no open, rebuild or save
diagnostics. The generated pair passes 84 numeric checks and 24 ordered
live-light observations. The reconstructed native save preserves all 60
typed light fields within the documented tolerance. The real child depth
edit and the selected signed concentric mate remain intact.
[Native receipt](../measurements/2026/ConcentricParentLightsNative01.json)

The actual D01 parent still refuses with `assembly root contains unprojected
model content`. The [reciprocal note pair](ConcentricParentNotes2026.md) has a
separate host proof. The exploded-view manager, display state, model and
configuration names, and remaining revision and presentation owners are open.
[Whole-source prerequisites](ConcentricSealedAdmission2026.md)
