# SOLIDWORKS assembly tessellation control

Pass `include_tessellation=False` to `convert.open_document` to omit meshes
from a SOLIDWORKS assembly. This also removes mesh references from component
definitions and applies the option to linked documents. The assembly reports
zero returned meshes and omits the tessellation capability.

The reader still checks native cache evidence when deciding whether it can
inspect a component without its external source. Component source resolution,
diagnostics, and other returned data follow their existing rules. Leave
`include_tessellation` enabled if the caller needs cached display geometry.

Three focused SDK integration cases passed with Python 3.14.6. Two cases read a
tracked native assembly by path and from bytes. They verify mesh omission,
neutral document validation, and unchanged component resolution evidence. The
third case verifies mesh omission in a linked assembly with its own cache.

See the [SDK options](../../../../Reference/Overview/ApiReference.md) and the
[cache evidence gotcha](../../../../Gotchas/Conversion/Solidworks/Readers/AssemblyTessellationOptOut.md).
