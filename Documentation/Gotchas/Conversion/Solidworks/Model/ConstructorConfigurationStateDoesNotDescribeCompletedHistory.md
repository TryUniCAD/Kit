# Record configuration progress after history construction

## Expected

A constructor-zero configuration marker stays valid after features are generated,
and constructor-unsuppressed features will remain active when the file loads.

## Observed

The native configuration lookup can apply its default suppression state to a
feature whose persistent ID exceeds the configuration's processed marker while
rebuild is needed. The generated sketch and extrusion loaded suppressed even
though their feature constructors initialized them unsuppressed.

Native completed update stores `header.getHighestID()` in configuration `f85c`.
The getter returns the header's next persistent ID minus one.

## Workaround

Derive the active configuration's processed marker after the generated history
and parameters have allocated their IDs, before serializing the streams. Keep
feature state and the default suppression flag tied to their actual native rules.
The [native record](../../../../../re/solidworks/records/ConfigurationProgress2026.md)
and [prior measured suppression](../../../../../re/solidworks/measurements/2026/FreshPartModelAppearance.json)
separate this rule from pending generated-output acceptance.
