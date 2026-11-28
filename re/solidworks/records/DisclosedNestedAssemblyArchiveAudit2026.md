# Typed archive audit of the disclosed nested assembly sources

The two disclosed SOLIDWORKS 2026 SP05.2 sources contain seven unique definitions, including four assemblies. Their six scoped streams produce 42 byte-identical read/store checks with no unread tails. Config-0 and ResolvedFeatures also round-trip in sequence with the re-emitted object map. The audit retains the original source hashes, reports schema gaps and writes a sanitized JSON receipt. The corrected native replay independently reopened and rebuilt those same immutable files between healthy controls. [Typed audit receipt](../measurements/2026/DisclosedNestedAssemblyArchiveAudit01.json) · [Native source replay](../measurements/2026/NestedAssemblyDisclosedReplayNative01.json)

## Direct binary ownership and XML closure

`moAssembly_c.f68` supplies the direct, ordered `moReference_c` objects. Its length equals `f1560`. ModelHeader and Header2 both store the expanded occurrence count in `fc4` in these populated saves. Both hold the same direct external directory state. Config-0 seeds its map with the self object at slot 3, then the unique direct directory entries starting at slot 4. Repeated placements bind the same entry by object identity. Each entry describes its immediate target's real kind, full file identity and creation time, with `f48` equal to its direct use count and an unset selected configuration. Each occurrence carries its actual child configuration at `f3c0`. The directory timestamp fields `f60` and `f70` match the referenced document's self object and CMgrHdr2 respectively. [External directory and time sources](AssemblyConstruction2026.md#child-directory-timestamp-sources)

The resolved continuation preserves the map index and identity of each directory entry and occurrence inherited from Config-0. Its 16 main roots per assembly describe the ordinary feature roles. The direct occurrence objects reside in the carried Config-0 map. Their Config-0 `moExtFeature_c` stores a backlink to the occurrence. CMgr stores a separate contextual feature with the same persistent identity and a null backlink. The active configuration lists a self row followed by one context chain of length one per direct occurrence, in reverse order in all four saves. Each chain targets the direct occurrence in its immediate containing assembly, so descendants have their own configuration entries in their own files. Its stamp is `101 + f3f0`. A contextual file wrapper keeps the containing assembly's creation time and active configuration under its internal model name. The leaf's shared file record retains the saved file identity. [Contextual construction trace](OrdinaryOccurrenceConstruction2026.md)

The saved `fc48` and `fc50` default option objects have equal field values and separate identities. Each direct occurrence's options differ from the selected default at display-state fields `f48`, `f50` and `f64`. The pinned target-type branch identifies which default is selected before those changes. The equal-valued records leave the branch choice to the static trace. [Pinned subassembly selection](NestedAssemblyReferenceState2026.md#resolved-target-dispatch)

`COMPINSTANCETREE` covers the whole transitive model closure, with one XML file and model per definition. Each model carries that definition's direct occurrences and local transform. Expanding the XML paths visits the same ordered occurrences and repeated descendants as the binary hierarchy. The auditor compares each file identity, target configuration, feature ID and name, transform stamp and exact `.16g` transform text. Assembly-local XML axis limits come from that definition's `f1a18` and also match exact `.16g` text. [XML vocabulary](AssemblyInstanceTree2026.md)

| Assembly definition | `f1560` direct | `fc4` expanded | Directory target count | XML definitions | XML local occurrence rows | XML expanded paths |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RiseModule | 1 | 1 | 1 | 2 | 1 | 1 |
| SingleFrame | 1 | 2 | 1 | 3 | 2 | 2 |
| IndexModule | 2 | 2 | 1 | 2 | 2 | 2 |
| MixedFrame | 3 | 7 | 2 | 4 | 5 | 7 |

## Target state and bounds

For every occurrence, `f3e0` and `f3e8` match the child model header's `f40` and `f48`. The auditor computes both other stamps bottom-up from the child's actual graph. Geometry adds each direct target's recursively accumulated geometry stamp to the containing model's `f1300`, with addition modulo 2³². Transform uses the pinned `101` sentinel fold over the definition's own immediate `f3f0` records. Parts contribute their own geometry stamp and transform stamp `101`. The root and all child documents expose the same computed pair in their `dmConfigHeader_c` fields `f50` and `f4c`. All seven saved occurrences carry local transform stamp `102` and `f4b0 = -1`. [Pinned native getter operations](NestedAssemblyReferenceState2026.md#distinct-stamp-operations)

| Assembly definition | Own `f1300` | Geometry sum and `CMgrHdr2.f50` | Transform fold and `CMgrHdr2.f4c` |
| --- | ---: | --- | ---: |
| RiseModule | 104 | `104 + 112 = 216` | 102 |
| SingleFrame | 104 | `104 + 216 = 320` | 102 |
| IndexModule | 104 | `104 + 112 + 112 = 328` | 204 |
| MixedFrame | 104 | `104 + 328 + 109 + 328 = 869` | 306 |

Each `f370` matches all ten words of the actual child-local box. For a part the source is `f7f8`. For each subassembly target the observed `f1a18` and `f1a20` both match, since the two caches are byte-equal in all four saved assemblies. All four store both boxes with `f1a28 = 1`. Reusing the direct transformed-box fold with independent sphere union reproduced all four pairs within `2.7755575615628914e-17 m`. It matched all ten words exactly in RiseModule. Flattening MixedFrame's leaves and then boxing the result changed an axis limit by `0.0004757318729328719 m`. Recomputing its sphere radius from the saved axis limits changed that radius by `0.009390265121485414 m`. [Direct-child bounds gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ExternalReferences/NestedAssemblyBoundsUseDirectChildBoxes.md)

## Reproduce and qualify

Run the auditor in the Kit checkout's Python environment against the original `NestedAssemblySource01/Results` directory. The replay option additionally binds the exact corrected `NestedAssemblyReopen01/Inspection/DisclosedNestedReopenResults.json` at the sibling location by its pinned digest. It verifies every reopened sibling's hash against the source archive audit. Omit the option for the typed audit alone.

```sh
python -B re/tooling/sw2026/serial/AuditNestedAssemblySources.py "$NESTED_DISCLOSED_RESULTS" --bind-native-replay
```

The tool only opens the two enumerated disclosed source subtrees and the optional disclosed replay result. It reports `moContextChainComponent_c` and `su_CMapStringToString` as provisional where the research schema uses them. Config-0 and the part ResolvedFeatures paths also exercise bounded raw operations, which the receipt counts. The exact archive matches prove serialization and cross-stream relationships for the disclosed profile. Bounds omission, hidden or exploded configurations, writer construction of those contexts, and behavior on sealed sources require separate evidence. Nested writer construction awaits both sealed source locks. [Audit code](../../tooling/sw2026/serial/AuditNestedAssemblySources.py) · [Sealed cohort procedure](SealedNestedAssemblySourcePhases2026.md)
