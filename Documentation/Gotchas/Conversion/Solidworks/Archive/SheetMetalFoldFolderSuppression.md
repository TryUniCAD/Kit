# Compare the fold folder under its native flat pattern

SOLIDWORKS 34.4.1.1011 reported Sketch Transformation1 as unsuppressed before the A-only save and suppressed on an independent read-only reopen of the same archive. It reported Flat-Pattern1 as suppressed in both sessions. The unchanged geometry, rebuild health, and feature records do not explain the raw folder transition on their own.

Retain each raw suppression observation and capture the native tree relationship. Accept unchanged effective suppression only when both observations identify the same enclosing flat pattern by name, feature ID, and persistent reference, and both report that owner suppressed. Require exact comparison for the other features and for any folder whose owner is active or unverified. [Native capture procedure](../../../../../re/solidworks/records/SheetMetalCapture2026.md)
