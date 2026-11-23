# Saved sweep Section sheets have sparse transmit order

A saved Standard sweep can carry a complete ten-cell embedded Section sheet
whose root has a next-body reference to non-resident slot 2. The measured
native transmit emits face slot 8 after slots 9, 10 and 11. The cold circle
constructor creates a dense, freshly allocated sheet for its distinct
archive context.

Preserve the typed saved resident order when checking byte identity. Permit
the absent next body only in the actual sheet root and validate every other
link against the resident cells. The Section is re-encoded through the
shared typed kernel encoder and compressed framing.
[Saved resolved proof](../../../../../../re/solidworks/records/AggregateSavedSweepRead2026.md#exact-saved-resolved-re-emission)
