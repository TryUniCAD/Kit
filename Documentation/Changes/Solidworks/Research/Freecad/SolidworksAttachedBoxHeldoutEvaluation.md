# Evaluate held-out Top-plane boxes

The [held-out evaluator](../../../../../re/tooling/sw2026/attached_top_box_source/EvaluateAttachedTopBoxHoldouts.py)
checks the original native source hashes before projection. It feeds a
neutral-only request to the separately frozen shared writer. It confirms two
identical guarded builds, then observes the generated part and its independently
edited saves in the versioned SOLIDWORKS 2026 guest.

The evaluation targets the signed sketch, actual Top-plane and origin owners,
three driving dimensions, reversed blind boss and solid geometry. The original
and edited native source models stay inside the guest. The
[source receipt](../../../../../re/solidworks/measurements/2026/AttachedTopBoxSourcesNative01.json)
binds the pre-writer hashes. See the [packet procedure](../../../../../re/tooling/sw2026/attached_top_box_source/README.md#evaluate-the-locked-sources).
Native held-out observations are pending.
