# Disclosed concentric parent root and provenance audit

Task `B04-SW2026-MATES-CONCENTRIC`, delivery PR #121. The normal source assembly admission still refuses D01. This audit binds all public parent feature rows to their actual typed owners and corrects the public display-state label. No sealed design or new native process was used.

## Exact parent owners

The [host audit](../../tooling/sw2026/para/concentric/AuditConcentricParentRoot.py) uses the normal SDK assembly reader, the Config-0 graph and the linked resolved-feature roots. The already measured [radial assembly lifecycle](ConcentricRadialAssembly2026.md) supplies the generated file and its native-saved derivative. The numbers below are results of matching persistent IDs, with no assumed numeric ranges.

| Owner | Native D01 source | Frozen generated parent | Native-saved generated parent |
| --- | ---: | ---: | ---: |
| Resolved-feature roots | 16 | 16 | 16 |
| Nested environment members | 4 | 0 | 4 |
| Nested annotation members | 2 | 0 | 2 |
| Empty exploded-view manager | 1 | 0 | 1 |
| Occurrence aliases | 2 | 2 | 2 |
| Total public feature rows with typed owners | 25 | 18 | 25 |

The resolved environment folder is the actual Config-0 `moAssembly_c.f1e0` object in all three snapshots. Its source and saved-derivative lists share four exact typed light intents after excluding creation clocks. Both annotation lists pass the reciprocal empty note-head/end owner checks. Both saved parents carry an empty `moExplViewManager_c` at `f1590`. Its two optional objects are absent, its `f368` map is empty, and its scalar state agrees. The frozen parent leaves that pointer null. These observations establish native regeneration of those ordinary defaults for the measured pair. Custom presentation and populated exploded views need separate construction and direct source comparisons.

The SDK places one ``solidworks.mates`` `mate-list` retention record in `brep_payloads` for each snapshot. Its declared count and observed record count are both one. This record carries mate evidence. The root has no decoded B-rep or standalone body. The typed selected mate, where admitted, must supply both actual occurrence and face owners before classification of retained bytes can proceed. Keep the source retention and informational archive diagnostic intact during admission.

The saved D01 `moAssembly_c` internal name is `Assem1` and its public file identity is `ConcentricD01AlignedFree`. The native manager selects the actual `Default` configuration through both pointers. The synthetic parent uses `AssemblyActive`. Retain and reconcile these distinct name and configuration roles when constructing a true source-derived parent. The ordinary root guard continues to refuse the source inventory and provenance.

## Display-state projection

The native source and the native-saved generated parent each carry `swDisplayStateName="Display State-1"` and `swShowState="Yes,Yes,"`. Before the correction, both projected an empty display-state name. The public route now reports `Display State-1` and retains the original attributes. The frozen parent still has no display-state row. The [existing assembly XML integration case](../../../tests/Convert/Solidworks/Research/Assembly/XmlIndexTests.py) exercises both source attribute spellings through normal open, with the modern spelling taking precedence. Black and diff checks pass. The repository integration case awaits remote execution.

| Host artifact | SHA-256 |
| --- | --- |
| Audit tool | `b97eb514d649358cf1ad21aeffa9e542842d89ac2f8baa4014075ea9bf47cac5` |
| Corrected three-parent audit | `698c5f8a3d731ded531cddd5fdd82fc075a146a2f948adfc0cfd68efee085656` |
| Existing native lifecycle receipt | `3263e7d2019953bede2c36948b84274d915b9cd8f4de1afc0bcb1988e0397f03` |

## Saved endpoint refusal

In this audit the public reader admits the D01 typed solved mate and reports the expected pre-solve refusal on the frozen generated parent. The native-saved radial parent reached the cylinder-frame check and refused a direction mismatch. Its selected wrappers store `fe8` and local `f108` along `+Z`, while both inherited placements transform the actual saved kernel carrier axis to `−Z`. Both world points match their expected geometry within `7e-18 m`, and both radii equal 7.19 mm. The original D01 has matching `−Z` directions in both domains. Subsequent public readback admits the saved pair while preserving its signed endpoint intent and authored alignment. [Saved orientation rule and measured readback](ConcentricSavedAxis2026.md)
