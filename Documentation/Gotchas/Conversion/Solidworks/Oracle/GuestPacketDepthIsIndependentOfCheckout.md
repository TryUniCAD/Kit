# Guest packets can run from a shallow Windows path

The frozen material origin retry stopped at import with `IndexError(5)` when staged under `C:\KitMatRetryMethod01\Tools`. Its repository freeze mode needed the checkout ancestor, but the staged guest runner used that lookup eagerly even when running from a standalone packet. The failure occurred before any native process or protected input read.

Resolve the checkout root within the host freeze operation. For an already frozen packet, preserve its exact bytes and use a guest staging path with sufficient ancestry. Both approaches keep the original private plan and generated candidate hashes fixed. [Retry procedure and scope](../../../../../re/solidworks/records/SealedMaterialOriginRetry2026.md)
