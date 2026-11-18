# Cache-free blind pocket geometry

The default SOLIDWORKS 2026 reader reconstructs the closed solid of a cache-free rectangular boss with one interior blind circular cut on its actual Front Plane. The planar entrance has a circular inner loop. An inward cylinder and a planar floor bound the cavity. The existing history and its live depth and sketch drivers remain available.

Use `convert.open_document` with its default B-rep option. The result carries the `sldprt.brep_reconstructed` diagnostic with the native boss, profile and cut owner evidence. The analytic result preserves the stock bounds and computes volume and surface area. Files with a readable native partition retain that geometry.

Eighteen independent path and byte reads passed. Three generated cache-free designs matched the native topology, volume, area and centre of mass. Six stored-partition files retained their existing native geometry. The public pocket writer and original held-out evaluation remain open.

[Adapter usage](../../../../Reference/Adapters/Solidworks.md) · [Field and geometry record](../../../../../re/solidworks/records/SdkBlindPocket2026.md#cache-free-solid) · [Process and oracle receipt](../../../../../re/solidworks/measurements/2026/SdkBlindPocketBrepRead01.json)
