# Imported body topology contrast

The exact SOLIDWORKS 2026 SP05.2 oracle authored and freshly reopened two
translated, differently oriented cylinders as ordinary local `BaseBody`
features. Both source phases and both controls passed. Each part contains
two planar caps, one analytic cylindrical face and two boundary edges.

The offline comparison reproduces seven linked streams per source using
the shared archive and local kernel codecs. The body tracking tag differs
between the box and cylinder sources while the display mode stays at six.
The local `BODY_MATCH` attribute appears in both cylinder saves. The box
has the same pair of archive tracking fields and omits the local attribute.
Fresh tag allocation and native imported-part construction remain open.
[Procedure and evidence](../../../../re/solidworks/records/ImportedBaseBody2026.md#analytic-topology-contrast)
