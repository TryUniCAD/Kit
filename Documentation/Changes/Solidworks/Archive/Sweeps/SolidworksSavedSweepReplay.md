# Re-emit the typed saved sweep resolved archive

The SOLIDWORKS 2026 part archive writer can explicitly re-emit the resolved graph of the two disclosed saved Standard sweep fixtures. It uses the actual inherited Config-0 map, the saved display and reference layouts, and the ordered resident records of the embedded Section sheet. It computes both levels of section framing and reconstructs the two binary64 display caches through the typed scalar writer.

The guarded offline proof reproduced both complete `Config-0-ResolvedFeatures` streams and matched their maps. It also reproduced an ordinary ladder stream and both prior cold sweep archives. The scope is the saved resolved stream in the specified context. [Evidence and reproduction](../../../../../re/solidworks/records/AggregateSavedSweepRead2026.md#exact-saved-resolved-re-emission)
