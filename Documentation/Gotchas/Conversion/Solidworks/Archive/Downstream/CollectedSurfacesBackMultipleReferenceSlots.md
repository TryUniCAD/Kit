# Collected surfaces back multiple reference slots

Making a fresh surface object for each inline reference slot changes the archive maps even when the objects contain the same geometry and feature fields. In the ordinary batch path, native face and edge rows retain pointers to the representations already cloned by the collector.

Construct the collector's surface objects once in linked entity order. Use those same object identities in each indexed reference and retain each inline wrapper, including the face loop separator. A collector-backed prism with six face rows has six shared surface identities and 30 nonnull face slots. [Source and guarded replay](../../../../../../re/solidworks/records/DownstreamCollectedSurfaceOwnership2026.md)
