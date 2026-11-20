# SOLIDWORKS local body readback

`convert.open_document` with B-rep enabled reads a single planar solid from the
SOLIDWORKS 2026 SP05.2 Config-0 local body stream when the active partition has
no bodies. The reader first gives the existing payload decoder its usual
selection. The local route then checks the active partition and history, reads
the complete typed local graph, and builds neutral geometry from its native
links.

This scope covers linear edges, planar faces with one loop each, and a single
closed solid. The local route requires all topology references to resolve.
Metadata-only reads continue to use `include_brep=False`.

Four disclosed rectangular and concave parts returned the expected topology.
Their volume, area and centre of mass agreed with the independent native
measurements. The attributed native import control retained exactly its
existing neutral B-rep. [Readback evidence](../../../../../re/solidworks/records/SdkImportedLocalBodyReadback2026.md)
