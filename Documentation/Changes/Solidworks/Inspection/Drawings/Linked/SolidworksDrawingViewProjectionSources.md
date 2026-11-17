# SOLIDWORKS drawing view projection sources

[DrawingProjectionSpecs01.json](../../../../../../re/tooling/sw2026/DrawingProjectionSpecs01.json) defines four disclosed drawings for the existing SOLIDWORKS 2026 source author. Each uses the pinned single-sheet template and referenced part. The cases independently select Front, Top, Right and Isometric with non-unit view scales and asymmetric sheet positions. The author records actual model-to-view transforms, outlines and linked geometry through native edit, save and fresh reopen.

The specifications are recognized by [AuthorDrawingSources.py](../../../../../../re/tooling/sw2026/AuthorDrawingSources.py) as discovery cases. Its source job supplies the template, reference part and control hashes and an unused output path. The discovery packet supports comparing actual wire values with the source-derived view rotation and scale rules. Existing sealed source specifications and native files stay in their original custody.

The source author and case specifications have been verified on the host. The ratio field bindings and the drawing-side creation routes are documented against the pinned binaries. [Source rules](../../../../../../re/solidworks/records/DrawingScaledViewProjection2026.md) Native observations and expanded generated view qualification remain open.
