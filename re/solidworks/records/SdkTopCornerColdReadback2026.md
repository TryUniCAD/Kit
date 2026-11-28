# Cache-free signed Top box readback

This PR #121 task prepares the axis-free anchored Top rectangle on SDK base
`9eb5a40b67406ea9b5a306e3cc5074d013096e66`. It uses the existing typed
readers, the anchored rectangle composer and the complete unchanged-source
comparison. The separate FreeCAD F14c publication route still owns three
additional selectable origin axes. [F14c publication](AttachedBoxAxisPublication2026.md)

The full public read links the Top support and its sketch to the creating
boss and one modeled solid. Two length drivers belong to the actual
sketch feature. An independent height driver belongs to the boss.
The typed origin point and active coincidence retain the origin anchor
through an explicit neutral sketch. Reconstruction uses the metre words
for the sketch drivers and the same inverse as the ordinary boss for its
depth. It retains the authored body name from the bound output atom.
The original document stays intact for a complete regenerated SDK
comparison. Any changed source content, regenerated hash or extra domain
that differs prevents preparation. The design-only view lacks the bound
body name. [Design-only body name](../../../Documentation/Gotchas/Conversion/Solidworks/Profile/TopDesignNeedsBoundBodyName.md)

Run the standalone disclosed proof from the checkout root.

```sh
python3.14 -I -B re/tooling/sw2026/attached_top_box_source/VerifyColdTopBox.py
```

The three input triples in millimetres are 20/30/10 from the disclosed
geometry, 17.125/28.375/6.625 and 17.103/24.625/12.25. The latter two are
independently authored comparison requests. Each has ten exact streams,
19 native feature rows, two sketch drivers and one editable boss depth.
The independent signed box equations agree with the observed volume, area,
centre and corners. Each guarded process regenerates its complete
container from the full strict public read with zero construction reads
and no CAD runtime. The first two complete files also matched the output
of the historical parity SDK at `cc9bad9637dad4281a4e41b28e7b6fdb29dd0fc5`
on the same Mac interpreter. The last request moves the displayed length
by one ULP and still reproduces the original archive.

The proof records 27 refusals across design-only input, changed body name,
unknown model metadata, wrong origin endpoint, wrong dimension owner,
changed archive clock or locator, and both public writer entry points
without the required measurement. The latter calls leave a pre-existing
stream untouched. No native acceptance or FCStd conversion credit is
recorded for these three files. [Guarded receipt](../measurements/2026/SdkTopCornerColdReadback01.json)

## Previously measured source slots

Both original native SLDPRT source hashes preceded the frozen writer
revision at `46f2463dfae91263143b24fb98531e610d929f63`. The exact SP05.2
oracle batch had six distinct processes, two healthy controls, 726
numeric comparisons, and eight native saves and reopens. The complete
generated output SHA-256 values were
`2a4a1e9a45197b2b93b4d63f8d054be460b4bd83be51ba18257e2c78d4c90b28`
and `a9069ba24a39ea8f52380e7f63e287b8dfb4dd5d58829c7cf24f5fe79270d680`.
The normalized held-out receipt is pinned at
`b50eb4668453ab4698f9bed0289809ba347b43a78c580a0646b8c3e0f3b6be38`.
[Pre-writer held-out native lifecycle](../measurements/2026/AttachedTopBoxHeldoutNative01.json)

A source-frozen guest comparison after that run regenerated both exact
files through the direct and registry streams with explicit portable
origin binding. The normalized parity receipt is pinned at
`7e665b19a2e957a68eea8d546e8b6af1b3a372e7940a1dd45ddcc366aef4f771`.
The guest retains the exact original neutral request, logical locator
and creation clock. The tracked receipt carries their evidence hashes.
The current authenticated plain-part publication expects its own
standalone schema and case reports.
[Historical public stream comparison](../measurements/2026/SdkTopCornerPublicParity01.json)

The delivery exit for these two slots is a guarded comparison on the
exact current SDK using the original guest-bound neutral requests.
That comparison can reuse the earlier hash verification and explicit
anchor projection, and must match both complete native-measured hashes
and each stream. A family publication check can then authenticate that
measurement before output. New locators or clocks require their own
exact output evidence. [Prior guest procedure](SdkFreecadOriginBox2026.md#locked-native-top-plane-boxes)
