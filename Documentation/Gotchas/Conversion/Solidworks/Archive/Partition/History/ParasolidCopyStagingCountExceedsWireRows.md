# Parasolid copy staging count can exceed wire rows

## Expectation

The i32 before the previous-state records gives the number of following serialized copies. The PMARK copy modification count gives the same number.

## Actual behavior

The two disclosed 2026 two-stock cut histories store a copy staging count of 76, emit 73 previous-state records and store 26 in the PMARK header's copy modification field. The pinned kernel writes the staging count, filters copy kinds inside the loop and writes a separate terminator. It temporarily substitutes a processed count for the PMARK header before writing the rollback.

## Workaround

Keep the header count, staging count and physical row inventory separate. Read to the actual terminator within the staging bound. Verify the class and ownership of each restored, removed and changed slot against its actual historical state. A generated file also needs the native allocation and filter rules that produce the staged and processed counts. [Exact trace and measured receipts](../../../../../../../re/solidworks/records/ThroughAllMultiStockHistory2026.md)
