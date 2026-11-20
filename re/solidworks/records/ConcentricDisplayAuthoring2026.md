# Authored concentric display states and cold reopen

The native cold open of the saved D01 display-state parent returned a document, error 0 and warning 32. The strict observer stopped before checking the returned document path, live display states or rebuilt geometry. Both native bracket controls passed. The native author verified the separate named and active visibility vectors and completed both owned-parent saves with zero errors and warnings. [Numeric receipt](../measurements/2026/ConcentricDisplayAuthoring04.json) · [Official load warnings](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swFileLoadWarning_e.html?id=3b36a39206d34f468a0d2c24bef11595)

Task `B04-SW2026-MATES-CONCENTRIC/parent-display-state`, owner `assembly_frontier`, delivery PR #121. The host audit binds the exact before-author and final parent saves from packet `ConcentricDisplayVisibility04`, the single owned child and all five phase records. The author wrote both parents at the same native destination. It kept the original all-visible default active at both saves. The audit ran on the disclosed host files and read no held-out sources. [Authoring protocol](ConcentricDisplayOraclePlan2026.md) · [Prior display-owner audit](ConcentricDisplayState2026.md) · [Audit tool](../../tooling/sw2026/para/concentric/AuditConcentricDisplayAuthoring.py)

## Exact saved visibility owners

The selected binary `moConfiguration_c` is the shared CMgr `f360/f368` target with persistent ID 0 and name `Default`. It joins XML configuration ID 1 and root model ID 2 through `swID` and `swModelRef`. The actual `moAssembly_c.f68` references supply persistent IDs 24 and 25, represented by XML reference IDs 4 and 7. Both references target the same `Default` child configuration and share one `moReference_c.f3b0` directory object, child model ID 5 and child file ID 6. The XML list has ID 8 and `swCompNameList="24,25,"` in both saves. The document's active-configuration display-link policy was false in the author. [Instance-tree field mapping](AssemblyInstanceTree2026.md)

| Saved name | XML leaf ID | XML show tokens for 24, 25 | Visual state key | Visual occurrence word `f10` for 24, 25 |
| --- | ---: | --- | ---: | --- |
| `Display State-1` | 9 | `Yes,Yes,` | 1 | `1,1` |
| `VisibilityFirstOnly` | 10 | `Yes,No,` | 2 | `1,0` |
| `VisibilitySecondOnly` | 11 | `No,Yes,` | 3 | `0,1` |

The three named native reads and the three independently activated native reads agreed with these vectors before and after the author save. The XML `swHidden` remains `NO` and the binary reference `hidden` word remains zero on both occurrences in both files. These base fields describe the all-visible saved default in this profile. The two mixed vectors belong to the new named rows. The KeyWords stream contains no separate row for the three state names.

VisualStates stores occurrences in order 25, 24. Each context chain resolves its actual `moExtFeature_c.f44` and name to the binary occurrence and the XML reference. The sole `f118` association stays `0 → 1`; the `f0f0` table changes from one row to three rows with independent IDs. Each component map and each of the three actual principal-plane maps carries outer keys 1, 2, 3. Plane handles bind ID and creation seconds to the actual plane records. Their state words stay `(0, 6, 1, 0)` for each key. The component words follow `(visibility, 6, 0, 1)`.

The outer map key selects named values. The attribute objects' inner `f08` stays 1 even for map keys 2 and 3. All six component map rows alias the same `visStateDisplayStateAttribute_c`, whose separate `f18` remains 1 and whose label remains `<Default>_Display State 1`. All fifteen component and plane map rows alias the same null-appearance object. The visible component object is shared by both default rows and the two visible mixed rows. The two hidden rows, `(occurrence 25, key 2)` and `(occurrence 24, key 3)`, share one new `visStateVisualStateAttribute_c`. All nine plane rows alias the same plane-display object. Use actual object identity and the outer state keys when comparing these aliases.

## Typed byte accounting and locator effects

| Stream | Before bytes | After bytes | Exact typed growth |
| --- | ---: | ---: | --- |
| `swXmlContents/COMPINSTANCETREE` | 2,623 | 2,801 | 88-byte first leaf, 89-byte second leaf and one extra count digit |
| `ThirdPtyStore/VisualStates` | 1,327 | 1,593 | 118 state-table bytes, 56 component-map row bytes, 20 shared hidden-object body bytes and 72 plane-map row bytes |
| `Contents/CMgr` | 3,310 | 3,540 | 230 locator bytes |

All six decompressed stream instances re-emitted byte-identically through their respective typed parses. Both VisualStates instances have zero opaque bytes and zero unread tails, with three provisional research schemas. Removing the new typed state table and map rows from the in-memory visual graph reproduces every baseline byte. The new hidden object occupies 22 bytes including its class-reference tag. Its body adds 20 bytes compared with an existing object reference. The map counter rises from 39 to 40. The parsed after-save XML re-emits the baseline after removing the two leaves and restoring object count 9 and the two model stamp values. The receipt also records all 24 changed, added and removed container stream-name entries.

The visual `moExtFeature_c.f10.h18` and context `moContextChainComponent_c.f40.shared.h18` alias the same empty path handle in both snapshots. The parent ModelHeader separately contains its full saved UNC path. The two visual `h10` titles are distinct handles in both snapshots. The external title matches the saved parent, and the context retains `Assem1`. Their file signature still joins the parent header. These aliases contribute zero bytes to the observed growth. This differs from the path/title alias splits measured in the prior D01 depth-edit save. The `CMgr.f1f8` raw string grows from empty to the same 115-codepoint parent UNC locator in UTF-16. Its two other changed fields retain their widths, configuration `f860` moves `106 → 114`, and assembly mass-cache `f18` moves `109 → 111`. CMgr has no alias split or merge in this comparison. [Prior path/title split](ConcentricDisplayState2026.md#exact-d01-edit-save-difference)

Both saved parents already store the same mapped `Z:` child path in `moReference_c.f3b0` and the XML child file record. The author saw a UNC spelling after copying and before saving. The cold observer's stored dependency check resolved the `Z:` spelling to the exact owned child. No child locator rewrite occurred between the two saved snapshots. The owned child SHA-256 stayed identical throughout, and its own binary file identity still carries the original UNC locator. Its title, file kind and creation identity agree with the two parent references. The receipt preserves locator hashes and kinds only.

## Warning 32 and the next causal contrast

The documented bit 32 is `swFileLoadWarning_NeedsRegen`. The packet has four distinct native processes. The leading and trailing controls each completed 14 numeric checks. The author completed 28; the cold return stopped observation at zero. The warning's actual native publisher and predicate remain unresolved. [Assembly regeneration publisher map](AssemblyNeedsRegen2026.md) · [Official load warnings](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swFileLoadWarning_e.html?id=3b36a39206d34f468a0d2c24bef11595)

The child's persisted `ModelHeader.f40` and `ModelStamps` update word are 134. Both parent `moReference_c.f3e0` words and the XML child `swLastModifiedStamp` are 148 in the default-only snapshot and 162 in the final parent. The stored reference-to-child deltas are 14 and 28. `moReference_c.f3e8` agrees with the corresponding parent save seconds in both snapshots. Root update words agree with the XML root and selected CMgr values at 106 and 114. This identifies a persisted mismatch that predates the new states. Only the final parent received the measured cold open. Prior child-first controls establish a warning intervention on separate assembly profiles. [Reference staleness and paired save measurements](AssemblyRebuildDecision2026.md)

Use a fresh owned copy of D01 at a single canonical parent and child destination for the next batch. Verify the native resolved paths against both owned files. In one author session create the same states, restore the default, rebuild and record the loaded child's actual update stamp `X`. Save the parent while keeping the old owned child file. Snapshot the old child. Then save only the loaded, explicitly owned child. Require the parent SHA-256 and both display streams to stay exact and the new child's persisted `f40` to equal `X` and the saved parent `f3e0`. Abort the paired-save contrast if the save changes this equality or the child identity, configuration or geometry.

Use two cold processes for the same exact parent bytes and same parent/child locators, first with the stale child snapshot and then with the synchronized one, with the original D01 controls before and after. Switch the owned child snapshot only while the oracle is closed. Record both native returned paths, IDs, update stamps and rebuild flags before any rebuild, plus the named and active visibility vectors and the normal geometry and mate checks after restoring the default. A diagnostic read may record observations after warning 32. The strict lifecycle requires warning zero. Clearing 32 only when child/reference stamps agree would demonstrate the intervention for this profile. A surviving warning calls for the mapped publisher trace.

Once a synchronized parent reopens cleanly, use the same parent/child locators for two independent research contrasts. Invert one named visibility vector in the XML leaf only for the first. In a separate contrast, switch the two joined visibility-object references for that outer key in VisualStates only. Keep both vectors distinct from the default and verify exact bytes of the unmodified display stream. Cold applicability and named/live readback determine precedence. Cache omission requires its own measurement. The current paired save changed both streams and has no native cold visibility observation.

The subsequent fixed-parent child comparison clears warning 32 and
recovers both mixed visibility vectors on a clean cold reopen.
[Child synchronization result](ConcentricDisplaySync2026.md)

## Host replay

```sh
python3.14 -B re/tooling/sw2026/para/concentric/AuditConcentricDisplayAuthoring.py \
  /private/disclosed/ConcentricDisplayVisibility04 /tmp/ConcentricDisplayAuthoring04.json
```

The output path must be unused. The retained numeric receipt has SHA-256 `1b008f32adcaaadd61a1d072ae3a012f8136418a5a6a9fe51b8fc65c2228587a`. It records the source hashes, phase hashes and exact typed data behind this partial domain result. [CAD acceptance criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Corpus correlation](../../Playbook/CorpusCorrelation.md)
