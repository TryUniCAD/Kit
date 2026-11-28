# Typed saved biography records

The shared version-19000 history codec reads and re-emits populated Biography streams. Each saved record holds ordered platform and build fields and two embedded start/end telemetry records. The ordered arrays determine their own counts. Use the existing `ReadHistMut` and `WriteHistMut` archive entry points for typed readback and byte verification.

The disclosed test checks four native-saved parts, one native-saved assembly, one native-saved drawing and one fresh generated part. All fourteen Biography and History streams re-emit exactly. Negative counts, a truncated record and an undeclared version reject. An independent 21-worker generation replay retains the exact through-all output bytes. [Receipt](../../../../../re/solidworks/measurements/2026/SdkSavedBiography01.json)

The fresh writer supplies an empty Biography record list. The native application adds its actual telemetry during its own lifecycle. [Field classification](../../../../../re/solidworks/records/HistoryConstruction2026.md)
