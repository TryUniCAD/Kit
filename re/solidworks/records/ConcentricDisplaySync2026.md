# Same-parent SOLIDWORKS display-state child synchronization

Saving the owned child clears D01's cold-open warning 32. The two controlled
opens use identical parent bytes and the same final parent and child
locators. Both native controls pass on SOLIDWORKS 2026 SP05.2
`34.5.2.0604`.
[Paired native receipt](../measurements/2026/ConcentricDisplaySyncNative01.json)

Task `B04-SW2026-MATES-CONCENTRIC/parent-display-state`, PR #121. The
[prior authored comparison](ConcentricDisplayAuthoring2026.md) established
the opposite state vectors in both saved archive owners and observed a
warning before checking cold visibility. This batch reuses the original
D01 controls and independently authors the same two states onto an owned
linked copy. The source pair's original hashes remain fixed.

The [guest observer](../../tooling/sw2026/para/concentric/ObserveConcentricDisplaySync.py)
saves the parent and retains the old child, then saves only that loaded
owned child and retains the new revision. The parent hash stays identical.
The [host gate](../../tooling/sw2026/para/concentric/PrepareConcentricDisplaySync.py)
pins both retained revisions and requires each parent reference's `f3e0`
and the XML child update stamp to equal the live child at 162. The stale
child has persisted `ModelHeader.f40=134`. The synchronized child has
`f40=162`. Both named display stream hashes agree across the pair.

| Cold read | Child stamp | Open error | Open warning | Parent needs rebuild | Numeric geometry and ownership checks |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stale child | 134 | 0 | 32 | 1 | 14 |
| Synchronized child | 162 | 0 | 0 | 0 | 14 |

Both diagnostic processes recover and activate the ordered vectors
`(1, 1)`, `(1, 0)` and `(0, 1)` on actual occurrences 24 and 25. The
independent named and live APIs agree. Restoring the default and rebuilding
preserves the model geometry, actual occurrence identities and mate. Five
fresh processes complete the author, both cold reads and the two controls.
The warning-bearing stale read is a contrast, with the synchronized read
establishing a zero-warning native lifecycle for this authored case.

The comparison changes the child save as a unit. Individual regenerated
child fields, display-stream precedence and model-only writer qualification
remain open. The batch reads no held-out assembly payloads and grants no
writer coverage credit.
