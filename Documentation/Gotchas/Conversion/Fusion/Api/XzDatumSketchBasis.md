# XZ datum axes are not the saved sketch axes

An origin XZ work plane and its default saved sketch frame share origin and normal, but their in-plane axes differ. In the six discovery and six held-out two-sided draft archives, the selected datum has U=+Z and V=+X; the saved UCS and owned DRMatrix have sketch X=+X and Y=−Z, with normal +Y.

Using the datum U/V directly rotates the profile incorrectly. Resolve the actual selected origin-plane recipe and reciprocal component ownership, then validate the saved UCS against the bounded default sketch relationship X=datum V and Y=−datum U. Compare its complete matrix with the owned DRMatrix and the recorded API sketch transform. Do not infer attachment from coincidence alone.

The solid's saved BODY transform is explicit identity. Solid carriers and the saved profile sheet are already world placed; the single-sided sketch sheet remains local. Applying the UCS again to the BODY double transforms the geometry. Use the qualified sketch frame only to compare local/world geometry while preserving every original native record. [Frozen rule and source-bound proofs](../../../../../re/Fusion/DecodedPromotion20261127/DualFrameLive/README.md)
