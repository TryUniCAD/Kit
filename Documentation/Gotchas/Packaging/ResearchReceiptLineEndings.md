# Git text normalization changes raw receipt digests

## Expectation

A native JSON receipt covered by a byte digest keeps that digest after a fresh checkout.

## Actual behavior

Windows Fusion emitted CRLF in the original receipts. Kit's default Git attributes normalized those JSON files to LF. The parsed receipt values matched, but the original SHA-256 checks failed after a fresh checkout.

## Workaround

Keep the original receipt bytes in the research evidence directory. Scope a Git attributes exception to the affected receipts and verify the tracked bytes against the original manifest digests. The saved cuboid evidence fixtures use this layout. See the [receipt custody record](../../../re/Fusion/SavedCuboidRoundTrip/PublicBoundaryEvidence.md#source-custody).
