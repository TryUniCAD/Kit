# Compare plane-display discovery archives offline

The research comparator records exact clear-stream and typed-field differences between hash-pinned SOLIDWORKS archives.
It reuses the typed Config-0 codec and a separately labelled Definition schema observation.
It retains strict production Definition refusals and validates the private stopped-to-continuation receipt chain.

Use `CompareCapture.py` with exact source hashes and a fresh output directory.
A controlled-toggle comparison also requires its receipt and, for the recorded continuation, the exact preflight receipt.
The [procedure and evidence](../../../../re/solidworks/PlaneVisibility/README.md) give the full command and custody requirements.

Five fresh Python 3.14.6 comparisons completed successfully.
Two toggle comparisons produced identical complete reports.
Wrong source identity and unrelated preflight lineage each refused without an output directory.
The current same-session no-op changed four clear streams; the cross-session toggle changed 21.
The strict Definition reader refused the alternate renderer profile in every compared endpoint.
The schema-only observations do not relax that guard.

The [session-confounding gotcha](../../../Gotchas/Research/Readers/PlaneToggleContinuationRetainsSessionEffects.md) records the limitation.
The observed low-word difference does not establish a bit-17 rule.
This tranche adds no production serializer, source admission or native acceptance claim.
No CAD application was launched and no reserved holdout was read.
