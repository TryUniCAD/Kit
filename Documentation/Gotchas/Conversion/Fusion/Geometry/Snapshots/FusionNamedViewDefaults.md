# Named Fusion cameras do not specify the active viewport

Saved cuboids can store an ordered named-camera collection and separate default home, scene orientation, renderer and current viewport settings. A view named `HOME` is a record in that collection. Restoring the last screen view requires current viewport settings.

The two populated controls have four unmodifiable named views and empty active viewport fields. The two saved edit and restore controls also have empty active viewport fields, with a different default home and scene orientation even though they have no named views. The populated controls keep named camera projection `1` and a separate renderer projection of `2`.

Preserve the named views, camera values and ownership links in the [scoped camera request](../../../../../Changes/Research/Encoder/FusionSavedNamedCameras.md). Keep residual presentation state explicit. Compare coordinates as stored, since the `TOP` target has negative zero coordinates and the diagonal `HOME` view has an up vector that is not perpendicular to its look direction.
