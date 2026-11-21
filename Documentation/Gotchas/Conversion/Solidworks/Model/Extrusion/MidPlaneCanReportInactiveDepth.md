# Mid-plane can report an inactive reverse depth

On an ordinary forward mid-plane stock boss, `GetDepth(False)` returns
the value of a retained `f20` display even when the reverse end is
inactive. Its initialized value can persist after a real D1 edit,
save and reopen. A source-like null `f20` returns zero.

Determine the active driver from the end mode and its actual
`f18` display. In the matched selected-stock through-all trial,
omitting the inactive owner preserves the feature tree, live D1 and
native geometry. Treat the two kinds of stored state explicitly.
[Disclosed calibration](../../../../../../re/solidworks/records/ThroughAllStockSecondary2026.md)
