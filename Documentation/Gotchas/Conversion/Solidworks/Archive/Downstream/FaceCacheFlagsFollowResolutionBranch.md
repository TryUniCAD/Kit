# Face cache flags follow the resolution branch

An ordinary direct mode-0 face begins with `(f60,f64)=(1,0)`, flags zero and handle zero. The actual-part surface-map fast path publishes boolean zero, yielding flags `0x200` with handle zero. Full unique-candidate resolution publishes boolean one, sets flags `0x300` and stores the selected live `gcFace_w` handle at `f70`. The final `f64` is a filtered candidate ordinal.

Use the actual model and candidate path to select the fields. `clearEntCache` masks the cache flags and retains `f18`, `f60`, `f64` and `f70`. [Source record](../../../../../../re/solidworks/records/DownstreamStoredFaceState2026.md) · [Receipt](../../../../../../re/solidworks/measurements/2026/DownstreamStoredFaceSource01.json)
