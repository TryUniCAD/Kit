# Occurrence reference numbers match their names

The component index exposes a separate `swReferenceNumber`, and the portable reader retains it in `reference_number`. The ordinary writer derives that same value from the positive decimal suffix of the actual binary occurrence name. The number is independent of the placement order used by the writer.

Preserve the explicit string when it agrees with that suffix. Refuse disagreements, including noncanonical decimal aliases. Omitting the explicit field produces the same generated XML number and binary occurrence name. [Index mapping](../../../../../re/solidworks/records/AssemblyInstanceTree2026.md) · [Disclosed evidence](../../../../../re/solidworks/records/ConcentricOccurrenceNumbers2026.md)
