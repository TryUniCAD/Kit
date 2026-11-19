# Distinct surface owners can share a face key

The early downstream lookup compares the 32-bit hash of the inline surface text. A key hit can enter reconciliation and reconstruct an earlier wrapper even when deeper entity comparison finds different references.

Calculate both keys from the actual generated owners. For the ordinary fresh path, require a nonzero original and check each nonzero candidate key against earlier originals. Insert only the current original after both searches pass. Keep the null slots in the archive because the reference retains them. [Native lookup and comparator](../../../../../../re/solidworks/records/DownstreamFaceKeyOrder2026.md) · [Generated replay](../../../../../../re/solidworks/records/DownstreamPrismFaceStore2026.md)
