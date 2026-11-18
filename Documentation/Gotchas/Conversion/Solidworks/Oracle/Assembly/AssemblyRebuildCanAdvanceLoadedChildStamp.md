# A rebuild can advance a loaded child stamp

The generated paired-save comparison initially checked the referenced child's
`GetUpdateStamp` after rebuilding the reopened assembly. SOLIDWORKS can rebuild
its resolved child even when both saved file hashes stay unchanged. Comparing
that later stamp against the one recorded during child save can report a false
synchronization failure.

Verify the resolved child's exact path and capture its stamp immediately after
the parent opens. Compare this value with the earlier child save and record the
new value after the explicit rebuild separately. Require both file hashes to
stay unchanged in the read-only reopen. In the disclosed A21 run the saved and
on-open stamps were 144, and the explicit rebuild advanced the stamp to 158.
[Paired observation](../../../../../../re/solidworks/measurements/2026/GeneratedCombinedMateNative01.json)
