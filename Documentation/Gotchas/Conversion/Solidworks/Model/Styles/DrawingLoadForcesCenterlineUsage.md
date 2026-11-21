# Drawing load forces centreline usage

The fresh ANSI detail operation clears the centreline bit. It is tempting to expect the same bit after opening and saving an otherwise unchanged SOLIDWORKS 2026 drawing.

The current UI drawing loader explicitly sets `moDetailDefs_c.f20` mask `0x100000` for non-storing files through version 19000, after resolving the effective model detail owner. The condition does not inspect the ANSI/ISO selector. The raw save exposes the earlier runtime fixup, so the first saved file can differ while its drafting standard and geometry remain correct.

Keep the constructor and load-normalization operations separate. Compare the complete style graph and retain the difference. For a separately qualified drawing constructor, compute a requested load-normal form with the one-bit rule and prove the actual primary detail is the effective receiver. Do not replace the whole word, exempt it from strict comparison, apply the drawing fixup to every part, or silently claim preservation of explicit false centreline intent.

The [exact caller/setter/store ledger](../../../../../../re/solidworks/records/DrawingCenterlineLoad2026.md) records the version and receiver limits and links original-byte fingerprints. The [earlier save observation](FirstDrawingSaveNormalizesDetailState.md) remains valid as a measured effect; this record refines the native mutation phase. No new constructor or acceptance is enabled by this note.
