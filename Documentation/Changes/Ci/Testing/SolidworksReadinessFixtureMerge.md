# SOLIDWORKS readiness fixture integration

PR #121 now combines the current Windows fixture cache with its prepared-assembly readback path.
The fixture can warm a source/runtime-keyed cache, publish a prepared DLL, and load that DLL in a separate capture process.
Cold compilation stays before listener startup and the session deadline.
The existing cold-start containment, prepared-copy, capture and dispatch limits remain unchanged.

The owner-parent query uses the current native process snapshot.
The obsolete PowerShell parent-query script is removed.
The roadmap retains the current main snapshot and records the unmerged partial drawing reader separately.

The merge starts from PR head `6cf4d8a9ec216fdb82a873f5fffd3f2aa48d586b` and main `68cec987d0b720762ae95f2f92799eb113d23b44`.
Python 3.14.6 passed all 21 affected Windows process cases in 78.74 seconds.
The run covered cache contention and invalidation, prepared output, native parent observation, and both readback queues.
An initial attempt failed during temporary-directory setup; creating its required parent resolved that setup error.
Hosted CI, configured approval and merge-group acceptance remain separate gates.
This repair establishes no new CAD format or conversion qualification.

See [assembly cache behavior](ReadbackAssemblyCache.md), [fixture modes](../../../Gotchas/Ci/Windows/ReadbackFixtureModes.md),
and [the readiness claim](../../../Maintenance/ConversionBacklog.md#b08-sw2026-pr121-readiness).
