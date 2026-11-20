# XML visibility alone leaves the default display state

A generated radial concentric assembly with three named visibility
vectors in the XML instance tree opens cleanly. SOLIDWORKS 2026 SP05.2
reports only the default display state. Both native controls pass.

The corresponding generation with the binary VisualStates stream
alone exposes both named mixed states, applies them to the correct
occurrences and preserves them through a driving edit, save and fresh
reopen. Native save also populates the XML display-state list. Verify
the actual inventory and visibility on cold open before relying on a
saved XML list for this assembly shape.

[Controlled single-store measurements](../../../../../../re/solidworks/measurements/2026/ConcentricRadialDisplayStoresNative01.json)
