# One all-visible state in the concentric parent

Task `B04-SW2026-MATES-CONCENTRIC/parent-display-state` in PR #121.
The internal constructor uses the SDK base
`0cd00727bac5068f3a21df07d6e3981b6cef3f69` and the two disclosed D01
parent and child pairs from SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`.
[Design correspondence](ConcentricD01DesignBridge2026.md)
[CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)

Both native parents contain one `Display State-1` on `Default`.
The instance tree uses leaf ID 9 and lists persistent occurrences 24 and 25.
The independent binary store associates active configuration 0 with
state key 1 and addresses those occurrences in reverse order. Each
occurrence owns the measured visible flags `(1, 6, 0, 1)`. The existing
typed reader consumes and re-emits both exact native stores.
[Native display owners](ConcentricDisplayState2026.md)

The concentrically mated radial constructor takes one explicit
`AsmDisplayIn` named `Display State-1` with a true Boolean for each actual
visible direct occurrence. It retains the existing ordinary child and
aligned unlocked mate scope. The three-state radial profile still
requires both opposite mixed states. The planar profile retains its
own single-state rules.

| Generated owner | Computed relationship |
| --- | --- |
| Root state and attributes | One state key, associated with the actual selected configuration. Both occurrence rows use that state and its existing default label and visible flags. The null appearance owner and the separate datum flags follow the measured ordinary profile. |
| Occurrences | The actual generated reference nodes supply persistent feature IDs and names. The binary context sequence reverses the ordinary component order. Both live mate endpoints still select these same occurrences and the same generated child face. |
| Parent file | Both generated headers agree on the parent title and locator. Both new detached visual contexts and their external-feature aliases use the same generated file identity and pooled locator and title handles. The source-derived title is `Assem1` for the original and `ConcentricD01AlignedFree` for the edit. |
| Datum rows | Three actual generated principal planes are selected in reverse feature order. Their two generated headers supply the existing both-empty-log value `2592000`. The native source's historical plane events remain in the source evidence. |

The constructor adds only `ThirdPtyStore/VisualStates`. The earlier
mixed-state discriminator measured this binary carrier independently
of the instance tree. The present singleton is an offline construction
with an independently decoded visibility state.
[Native binary-store control](ConcentricRadialVisibilityDiscriminator2026.md#single-store-experiments)
[Default-state gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/DefaultConcentricStateCanStandAlone.md)

## Guarded verification

Two fresh processes per disclosed state consume neutral requests at the
same explicit locators and creation epoch as the previous bridge. They
generate the previous parent and child byte-for-byte. The singleton
adds one stream with exact independent typed re-emission and preserves
all prior parent streams and the complete child. The 1,403-byte original
request store and the 1,439-byte edit request store each end at map 38.
The path and title check covers both parent headers and both visual
contexts for each request.

Removing only the modeled empty exploded-view manager in a separate
allocation contrast shifts both actual persistent occurrence IDs. The
binary contexts follow those new IDs and keep the same names and shown
actions. Each worker refuses a hidden or renamed singleton, a foreign or
repeated name, a numeric visibility, a two-state request, a detached
parent file alias and reordered actual occurrences. All four workers
record zero external access attempts. The prior radial three-state
proof still reproduces its measured display output and no-intent
baseline and refuses its 13 original negative cases.

The guarded planar worker also reproduced both disclosed A20/A21
planar pairs and its independently authored pair byte for byte against
the exact task base. All 72 logical streams matched. This comparison
used the same neutral envelopes in fresh workers against the current
checkout and a `git archive` of the pinned task base. The historical
planar supervisor's older baseline fails to deserialize the current
`OutputBodyIds` field before reaching display construction.

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01ParentDisplay.py \
  --disclosures /path/to/Oracle121Takeover
```

[Guarded receipt](../measurements/2026/ConcentricDefaultDisplay01.json)

## Source and publication boundary

The original parent instance tree still owns the original XML state.
The generated binary store uses the current model's file aliases,
flag-zero links and empty-log epochs. The source uses historical
visual file aliases and its actual creation events. The source child's
separate appearance store and radial presentation still require
independent model-owned construction. The unprojected native source still
refuses at the ordinary root's content guard. Current proof covers the parent
configuration and all-visible state only. A distinct native acceptance
batch is required for these generated bytes, and public publication
remains closed.
