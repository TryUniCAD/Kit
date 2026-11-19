# Older FreeCAD carriers include visibility in sketch replay digests

Earlier Kit readers interpreted a hidden native sketch as suppressed and included that state in the replay digest.
A current read of the same FCStd bytes reports a hidden sketch as active when the source has no explicit suppression.
The digest changes even though the archive content is identical.

Use the ordinary FCStd write route to restore the carried archive.
Kit checks the carried model, validates the original archive, and compares a fresh native parse with the stored digest.
If the current parse differs, Kit reparses with the older visibility interpretation, including sketches in linked native documents.
An edit changes the carried model digest and uses the normal rebuild path.
For a verified older carrier, Kit compares each unchanged sketch flag with the original native archive.
The rebuilt sketch uses the original explicit suppression state for an inherited flag.
Kit preserves suppression edits that differ from the older carried value.
Kit records the independently parsed current digest on the carried archive after migrating its sketch flags.
An unchanged linked child keeps exact replay when a portable export writes it beside the rebuilt parent.
A parent rebuild verifies each carried child independently when its original external file is unavailable.
If a child correction changes the carried model, Kit clears the unverified parent digest and retains independently verified child digests.
Newly read archives record the explicit sketch suppression profile.
When a historical carrier lacks a complete parent replay match, Kit can recover inherited parent flags from its validated native archive.
The fallback can rebuild the parent with corrected values while exact replay still requires the complete digest match.

[FreeCAD adapter guide](../../../Reference/Adapters/Freecad.md) and [restore integration cases](../../../../tests/Convert/Freecad/FreecadTests.py)
