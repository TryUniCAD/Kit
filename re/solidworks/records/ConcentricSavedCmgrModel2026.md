# Saved concentric occurrence state from actual model owners

Task `B04-SW2026-MATES-CONCENTRIC/source-cmgr-history` in PR #121,
owner `assembly_frontier`, at base
`6d85ed1cb9ff6c033c5a0017dbfc49ffb52bc146`.
The source supervisor verifies the six previously disclosed parent and
child pairs from SOLIDWORKS 2026 SP05.2 `34.5.2.0604`. The guarded
construction uses both D01 neutral states and the existing named child,
radial text and signed mate constructors.
[CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) ·
[Previous detached-title proof](ConcentricD01RootHistory2026.md)

## Saved ownership and semantic projection

The selected configuration's self row and two reverse-registered
occurrence rows are distinct. Each live occurrence is an actual member
of the parent's `f68` list. Its external feature targets the current
parent title and locator plus the same creation identity as both
headers. The live backlink points to its actual occurrence. Each
detached target carries the corresponding actual ID and name. The
historical contextual file retains the earlier title and empty path
while sharing the same parent creation identity.

Both directory headers select the actual child by its file key,
creation epoch and separate save events. The live occurrence's
`f3e0`, `f3e8` and `f3f4` reference that child's actual header
update counter, update seconds and model geometry stamp. The
instance's `f3c0` and the manager row's `f28` join the actual selected
child configuration. The normal SDK resolves the same hash-pinned
child. No copy of the original Windows file path or source clock
enters the neutral writer request.

Each of the twelve occurrence rows has an independent child display
selection. Its `moConfig_c.f48/f50` pair is
`<Default>_Display State 1` and `1`. The child VisualStates
configuration association and actual state row own both values.
The parent insertion options retain an empty name and key `-1`.
The exact option differences are `f48/f50` and the existing
`f64=0` use-as-zone state. The row's `f18` enables the
`0x100000` present bit. The supervisor projects the selected
child state by its semantic name and neutral occurrence ID.
The worker derives its numeric key from the child it builds.
[Insertion option rules](OrdinaryOccurrenceConstruction2026.md#field-rules) ·
[Child display-choice gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/ChildDisplaySelectionHasItsOwnStateKey.md)

## Guarded construction from two neutral states

The prior and current neutral roots identify the same definitions,
occurrences, datums and mate. Their editable child depth and floating
placement carry the actual disclosed change. The worker joins those
placements by their owned neutral identity and adds one placement event
only to the changed occurrence. The current occurrence stamps are
102 and 103. Both separately generated contextual stamps are 203
through the earlier occurrence objects and the existing
`101 + placement stamp` rule. Both manager and visual contextual
files derive their earlier title and empty locator from the earlier
modeled state. All current target handles and child stamps derive
from the current parent and child.

The shared assembly emitter recalculates the aggregate transform
stamp as 205, and publishes the actual current occurrence stamps in
the instance XML. The new manager header's geometry stamp is 309
from the current generated root and child. The source's own geometry
history advances from 310 to 315. Its different internal update
clocks remain source evidence. Both produced files retain their own
modeled creation events.
[Aggregate stamp rule](NestedAssemblyReferenceState2026.md#distinct-stamp-operations)

| Owner | Exact generated comparison |
| --- | --- |
| CMgr | Two independently modeled child display assignments plus the two split historical string handles. The stream grows from 2,382 to 2,502 bytes. The exact typed comparison sees eight changed leaves and two alias splits. |
| CMgrHdr2 | The aggregate transform fold updates with the changed live occurrence. |
| Config-0 and component index | The actual current reference and its XML transform stamp agree. |
| VisualStates | The previous 1,449-byte detached-history stream reproduces at terminal map 40. |
| Other parent and child streams | All eight remaining parent streams, including the actual signed MatesList, and all child bytes remain exact. |

Two fresh guarded writers generate the same complete 11,154-byte
parent and unchanged child, with zero runtime external accesses.
Changing the child display, child configuration or occurrence order
refuses before emission. Four separate guarded controls retain D02's
aligned lock and D03's anti-aligned free intent in both actual saved
states. The ordinary rich display guard refuses those controls
with their actual mate settings intact.
[Complete numeric result](../measurements/2026/ConcentricSavedCmgrModel01.json)

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveConcentricCmgrHistory.py \
  --disclosures /absolute/path/to/Oracle121Takeover
```

The bounded assembly already preserves modeled root and child
appearance and actual current mate geometry. A subsequent
[owned chronology proof](ConcentricD01AssemblyChronology2026.md)
constructs the original revision logs and feature instants alongside
these retained context roles. Original root inventory admission,
unclassified native metadata, update allocation, and native
validation of the combined bytes remain open.
`CheckAsmRoot` retains its whole-source refusal. This host work
does not add public or held-out qualification.
