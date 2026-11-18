# A timed-out Hopper startup does not prove document cleanup

Expectation: a private-copy REA query either returns its procedure or closes its own Hopper document completely.

Observed: the concentric serializer query timed out before the authenticated bridge appeared and reported incomplete cleanup. A separate shared request had already reported a foreign retained owner. Closing the logical binding did not establish that the native document was closed.

The uniquely titled task document was targeted through its own accessibility close control, then its discard and stop-disassembly prompts. The final readback showed no accessible windows while the application process stayed alive. That observation proves neither preservation of earlier shared documents nor authenticated provider cleanup. A private note that claimed preservation before checking was invalidated.

Use an isolated copy with a unique title, retain the original binary hash, and identify ownership before any close operation. Keep native window observations separate from provider session state. Do not terminate the shared application, close other documents, or report successful analysis from a startup timeout. If foreign ownership cannot be established, keep the remaining investigation stateless and report the cleanup limit.

The [custody receipt](../../../../../../re/solidworks/measurements/2026/ConcentricMateHopperCustody01.json) and [field record](../../../../../../re/solidworks/records/ConcentricMateConstructionSources2026.md) retain the exact evidence limits. No CAD or licensing process was touched by this analysis attempt.
