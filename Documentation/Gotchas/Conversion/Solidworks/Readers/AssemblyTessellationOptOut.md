# Assembly mesh filtering still needs cache evidence

An assembly reader should omit returned meshes when callers set
`include_tessellation=False`. The previous reader returned the cached meshes
and component mesh references regardless of that option.

Disabling the low level mesh read also removes evidence that strict assembly
inspection uses when it cannot load an external component. This can make a
valid assembly read from bytes refuse even though the cache contains a mesh.

Retain the native cache check and filter the returned meshes and references
when assembling the neutral document. Cache evidence does not establish that
an external component source loaded. See the [source resolution gotcha](../../SolidworksAssemblyResolution.md)
and the [tessellation change](../../../../Changes/Solidworks/Inspection/Assemblies/SolidworksAssemblyTessellation.md).
