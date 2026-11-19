# Older FreeCAD carriers include visibility in sketch replay digests

Earlier Kit readers interpreted a hidden native sketch as suppressed and included that state in the replay digest.
A current read of the same FCStd bytes reports a hidden sketch as active when the source has no explicit suppression.
The digest changes even though the archive content is identical.

Use the ordinary FCStd write route to restore the carried archive.
Kit checks the carried model, validates the original archive, and compares a fresh native parse with the stored digest.
If the current parse differs, Kit reparses with the older visibility interpretation, including sketches in linked native documents.
An edit changes the carried model digest and uses the normal rebuild path.

[FreeCAD adapter guide](../../../Reference/Adapters/Freecad.md) and [restore integration cases](../../../../tests/Convert/Freecad/FreecadTests.py)
