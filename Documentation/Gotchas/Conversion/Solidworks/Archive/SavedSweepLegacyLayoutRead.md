# Saved sweep fallback reads a packaged layout

A strict saved sweep uses the linked archive grammar and can run with all
external file opens denied. Malformed optional part XML sends a permissive
read to the legacy reader. That reader loads the package's
`convert/adapters/solidworks/Config/RootLayout.json` layout once during its
ordinary rectangle probe, even for a sweep.

The guarded fixture probe permits that exact path in read-only mode only
during the permissive branch. It counts one layout read per malformed XML
case. The strict full and design-only reads keep the complete file-open
guard. [Review evidence](../../../../../re/solidworks/records/ScopedSavedSweepSdk2026.md#review-boundaries-and-warm-publication)
