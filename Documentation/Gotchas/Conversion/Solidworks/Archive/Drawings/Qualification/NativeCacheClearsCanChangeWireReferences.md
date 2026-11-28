# Native cache clears can change wire references

An operation named `setLocalFeatureToNULL` can modify a field that is also serialized. In the drawing edge-map save path, the actual `moBEntRef_c` visits its entity IDs, then an embedded FR keeper clears its cached-feature pointer only when a persistent reference exists. The keeper serializes both the cached-feature and `moFR_c` pointers.

Calling that mutation runtime-only would incorrectly justify a wire-preservation claim. Applying it inside a generic raw codec would instead discard a source reference and potentially change subsequent archive-map allocation.

Retain source fields in byte replay. Keep the vendor's runtime save normalization, fresh-constructor rules and wire grammar distinct. The [native ownership proof](../../../../../../../re/solidworks/records/DrawingDetailingIndexRead2026.json) binds the complete setter, conditional leaf, FR-keeper serializer and actual drawing caller. It supplies no universal null writer default.
