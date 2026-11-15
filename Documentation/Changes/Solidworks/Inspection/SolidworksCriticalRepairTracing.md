# Observe the critical native repair path

The full native observation profile now records the application sites that select the critical repair error.
The staged clean inspection returned no document, error `0x400000`, and zero warnings between two healthy controls.
The [measurement](../../../../re/solidworks/measurements/2026/FreshPartStages.json) retains separate open start and return markers.

The observer records the confirmed repair-flag setter and the API comparison that maps this flag to the error bit.
Each event includes the application pointer, thread, instruction location, and adjacent raw 32-bit words.
The [repair record](../../../../re/solidworks/records/CriticalRepair2026.md) separates the error mapping from the unidentified format validator.

The module manifest now includes the exact 2026 application-module hash.
The existing full profile verifies that hash before hook activation.
No application preference or serialized value is inferred from this instrumentation.
Static JavaScript syntax inspection passed. New controlled hook results remain pending.
The production adapter remains read-only.
