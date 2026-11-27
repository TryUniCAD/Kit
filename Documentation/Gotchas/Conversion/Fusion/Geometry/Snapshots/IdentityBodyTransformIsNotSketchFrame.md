# Identity BODY transforms are not the selected sketch frame

The XZ two-sided circular sources store a nonidentity sketch UCS and DRMatrix. Their solved solid and double-sided profile sheet already use world carrier coordinates. Each BODY also references a separately allocated identity `TransformNode`. The single-sided sketch sheet remains in local XY coordinates and has no BODY transform reference.

Applying the sketch frame through those BODY records rotates the world geometry a second time. Replacing the identity nodes with the UCS, dropping them, or merging their equal numeric values loses source meaning or coverage. Certify every identity field, retain the original record and reference, and use a temporary transform-free BODY only when the existing shell walker needs a comparison view.

Check the profile sheet with the source-selected sketch basis and the sketch sheet with local identity. Preserve the full seam interval and endpoint, selected-circle attribution, passive root IDs and disjoint record coverage. The origin datum's tangent axes need not equal the selected sketch axes; qualify the actual source UCS through its owned plane recipe and DRMatrix.

The [frozen discovery and holdout rule](../../../../../../re/Fusion/DecodedPromotion20261127/DualFrameSnapshots/FrameRules.md) passes six discovery and six reserved XZ source states without refitting. The [results](../../../../../../re/Fusion/DecodedPromotion20261127/DualFrameSnapshots/Results.md) retain six encoded counterexamples for BODY rotation, translation, reflection, shared identity nodes, wrong profile normals and world/local sheet confusion. These are source-reading results, not native output acceptance
