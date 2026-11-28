# D01 root inventory and detached parent locator history

Task `B04-SW2026-MATES-CONCENTRIC/source-root-history` in PR #121,
owner `assembly_frontier`, at base `43b419d5c2d5a4a90731c26f90a87eafaa1012bc`.
Both exact disclosed D01 parents and their bound children come from
SOLIDWORKS 2026 SP05.2 `34.5.2.0604`. The source owner audit and guarded
construction use the existing shared typed container and mate model.
[CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) ·
[Design bridge](ConcentricD01DesignBridge2026.md) ·
[Child appearance](ConcentricD01ChildAppearance2026.md)

## Actual source admission chain

`CheckAsmRoot` refuses both SDK-read parents for unprojected model
content. The direct root has no own sketch, selection, solid, mesh,
material, B-rep or drawing. Three independent fields trigger its
first inventory predicate.

| Field | Exact owner |
| --- | --- |
| `feature_timeline` | 25 ordered public rows with 16 resolved roots, four nested environment members, two reciprocal annotations, one Config-0 exploded-view manager and two actual occurrence aliases. Names, public order and unique IDs bind the real typed owners. The empty exploded manager uses the keyword display alias with no model name node. |
| `brep_payloads` | One `solidworks.mates` retention record. Its payload identity, count, exact contents and digest agree with the archive's single typed `moMateConcentric`. The public mate points to that same payload. |
| `diagnostics` | One informational `sldasm.native_record_unresolved` record. The original independently admitted typed concentric endpoints remain in the graph. |

Separate diagnostic-only projections bypass each earlier predicate
in memory so the actual next message is observable. The following
four refusals concern source extensions or capabilities, document
metadata, assembly graph extensions and active configuration
extensions. Both original documents retain every field and their
exact read fingerprints. The stripped probes never enter the
constructor. The source metadata includes native source bytes
as independent retention, and generation never consumes them.

## Locator ownership across the actual two-state pair

Both typed headers in each source agree. The current path and title
go from an empty locator and `Assem1` to a 134-codepoint locator and
`ConcentricD01AlignedFree`. The assembly kind and creation identity
remain shared. The empty manager-level locator `CMgr.f1f8` is a
separate field in both saves. Each saved header has its model
present. The fresh model still uses the ordinary header pair with
presence on the model header only.

| Actual typed owner | Original | Edited |
| --- | --- | --- |
| Header self-file, and live `moReference_c.f4f8.f10` target | Earlier title and empty path | Current title and locator |
| CMgr detached `moExtFeature_c.f10` target | Earlier pair | Current pair |
| CMgr contextual `moContextChainComponent_c.f40.shared` | Earlier pair | Earlier pair |
| Binary VisualStates `moExtFeature_c.f10` target | Earlier pair | Current pair |
| Binary VisualStates contextual `moContextChainComponent_c.f40.shared` | Earlier pair | Earlier pair |

The two actual occurrences retain IDs 24 and 25 and the contexts
retain reverse configuration order. Target/context strings pool in
each original stream. After the edit each stream holds the separate
pooled current and prior string pairs. Both contexts keep flag
`f58=0`. The moved occurrence 25 advances from placement stamp 102
to 103. CMgr and VisualStates both retain context stamp 203, which
agrees with the earlier placement. The untouched occurrence stays
102. A native saved context can therefore point into a historical
state even while its real occurrence backlink is current. Treat
those context stamps as saved history.
[Existing VisualStates edit analysis](ConcentricDisplayState2026.md#exact-d01-edit-save-difference) ·
[Occurrence reference construction](OrdinaryOccurrenceConstruction2026.md) ·
[Placement stamp gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/SavedContextCanRetainPriorPlacementStamp.md)

## Model-owned research scope

The guarded extension accepts two neutral same-root models of the
ordinary D01 profile. Every design field agrees except the actual
floating placement and the independently owned blind depth. Root
definitions, fixed occurrence, datum order, face roles, mate and
configuration stay bound. The earlier contextual title comes from
that independently generated earlier root. The unlocated-path
branch encodes an empty string. The current title and locator come
from the actual current generated headers. The earlier source
artifact contributes no archive bytes, handles, object IDs, physical
path or native stamps to the worker.

The detached VisualStates composition retains the earlier title
and empty locator in its contextual file only. It computes both
current target handles and every live link from the generated
current parent. CMgr stays byte-identical to the ordinary generated
current assembly. The visual context stamps also follow the actual
fresh geometry owners. The prior pose is never installed as a
current placement stamp. Parent placement, complete mate bytes,
binary visibility, model-appropriate appearance and radial text
remain on the current generator.

The proof changes just the two detached string-handle leaves and
adds two map slots. With the six-codepoint D01 earlier title the
new stream grows from 1,429 to 1,449 bytes, following the two new
handle frames and one earlier UTF-16 title. The two cases preserve
all 12 other parent streams. The unrelated title grows its store
from 1,423 to 1,481 bytes. Four guarded workers observe zero
runtime input accesses. They refuse a stale current CMgr stamp, reusing the current
model as its own predecessor, crossed datum order and missing
placement/depth edits. Exact source replays preserve both original
headers, selected manager, binary display store and mate stream.
[Guarded receipt](../measurements/2026/ConcentricD01RootHistory01.json) ·
[Source owner audit](../../tooling/sw2026/para/concentric/ReadD01RootHistory.py)

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01RootHistory.py \
  --disclosures /absolute/path/to/Oracle121Takeover
```

The research output retains the earlier display title in the
detached carrier. Its live and manager contexts remain freshly
generated. Retaining the observed saved CMgr context lag, original
header and datum creation events, and original physical density
publication still needs separate evidence. Both source admission
and native qualification remain closed. The later
[saved CMgr composition](ConcentricSavedCmgrModel2026.md) also emits
the modeled prior manager context, actual child display selection
and the new current placement through the shared assembly emitter.
