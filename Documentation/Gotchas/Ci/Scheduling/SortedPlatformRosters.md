# Sorted platform rosters

Pytest collection order might appear suitable for a platform report roster.
The report verifier sorts the combined executed identifiers before comparing them byte-for-byte with `Collected.txt`.
An unsorted collected roster therefore fails even when every case ran exactly once.

Use the same sorted LF roster in process fixtures and production platform selection.
Keep the exact-once verifier intact.
See [runtime scheduling](../../../Changes/Ci/QueueRuntimeScheduling.md).
