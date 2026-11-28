# Construct the disclosed empty assembly exploded-view manager

Task `B04-SW2026-MATES-CONCENTRIC/parent-exploded-view`, owner `assembly_frontier`, delivery PR #121. The host proof covers optional presence of the ordinary empty manager under the actual assembly Config-0 model. Its exit condition is exact typed placement, one keyword row, unchanged prior outputs and rejection of unsupported placement. New vendor acceptance and complete source transfer remain open. [Guarded proof](../../tooling/sw2026/para/concentric/ProveConcentricParentExploded.py) · [Revision-bound receipt](../measurements/2026/ConcentricParentExploded01.json)

## Empty placement rule

The named native assembly constructor initializes `moAssembly_c.f1590` to null and `f1598` to zero. The existing assembly serializer reaches the optional view manager through `f1590`. The actual `moExplViewManager_c` constructor invokes the shared word-map constructor at `0x4baaa78d`. Its current-version tail stores two nullable objects, a distance scalar, two indices and the word map. [Native assembly initial state](AssemblyInitialRoot2026.md) · [Manager and word-map trace](CommonPartOwners2026.md)

The original D01, its independent depth-edit save and the native-saved radial parent contain the direct schema-one manager. Its two optional objects `f358` and `f360` are null. The distance `f398` is zero, both indices `f3a0/f3a4` are −1, the embedded `f368` map is empty and the model's `f1598` is zero. The frozen radial control retains the absent pointer. All three saved managers have one actual entry in each linked Config-0 and ResolvedFeatures map and zero entries in the resolved root sequence.

| Disclosed state | Persistent manager ID | Creation subservice | Creation clock |
| --- | ---: | ---: | --- |
| D01 original and depth edit | 1 | 0 | Source instant preserved by the edit |
| Native-saved radial parent | 26 | 0 | Unset |
| Frozen radial parent | — | — | — |
| New host-generated comparison | 23 | 2 | Unset |

The actual name pointer `f18` is null. The independent keyword index contains one `Feature` element with `Type="Exploded Views"`, an explicit empty `Name` and the allocated manager ID. The normal SDK presents a readable label using that ID. [Name-ownership gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Assembly/EmptyExplodedManagerNameComesFromIndex.md)

## Generation and verification

`AssemblySysIn.HasEmptyExplodedView` takes an explicit boolean. When present, the shared assembly composer initializes the nameless concrete node, allocates it after the optional light and note members and places it in `f1590`. Flat and nested keyword emitters use the same direct-owner check and name rule. The normal root and member histories keep their previously computed behavior. [Constructor](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/System/MakeAsmExploded.py) · [Keyword owner checks](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/Xml/AsmExplodeNode.py)

The proof overlays eleven SDK paths and one research runner on `b791b65c8dea2fc0c486aa0b47eea97ece4d9ce9`. Two independent builds of the scoped neutral request produce identical complete parent and child files with zero guarded file, process or network accesses. The three linked parent streams read and re-emit exactly and the signed concentric endpoint checks pass. Config-0 grows from 23,839 to 24,029 bytes and the public timeline from 24 to 25 rows. The four lights and two annotation members retain their typed values and allocated IDs. An additional host generation establishes independent presence with an otherwise empty light and note inventory.

The generated manager and all three saved managers agree on 39 typed fields. The receipt retains the other four fields as provenance and generated identity. `f08` comes from the actual persistent allocator. Two clock words come from the proven unset default in the independently native-saved radial manager. `f301` is the creation subservice from the explicit SP05.2 feature target. The saved controls' value of zero remains in their source evidence. [Creation version owner](PartChronologyConstruction2026.md)

The absent case reproduces the earlier notes, lights and empty-system hashes and eleven whole-file pairs across the older flat and nested controls. Twelve source or writer refusals cover stale placement flags, unexpected names, invalid boolean input, missing and foreign owners, duplicate IDs, flat roots and populated placements. Black, Ruff, full scoped steering and strict Mypy pass across the eleven SDK paths.

The actual D01 root still refuses with `assembly root contains unprojected model content`. The count of 25 by itself leaves the component-tree display-state list, the native VisualStates store, independent configuration and model names, remaining model presentation and source-specific provenance unresolved. Native reopening and editing of this new optional manager await a separate controlled lifecycle. [Previous parent audit](ConcentricParentRootAudit2026.md)
