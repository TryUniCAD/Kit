# Read back a SOLIDWORKS full-ellipse boss

The normal SOLIDWORKS part reader preserves one free full ellipse on the canonical Front Plane, its positive forward blind extrusion and the live D1 dimension in the ordinary Default configuration. Use `open_document` with its default options to receive an exact neutral solid with rational elliptical surfaces and trims. Set `include_brep=False` to receive the same editable sketch, feature and depth without constructing the solid.

The reader requires the complete typed cache-free profile. Stored native B-rep continues through the existing path. Raw extraction requires an actual native payload.

Both disclosed, native-tested SDK archives passed strict public readback and neutral JSON round trips. The reconstructed solids matched the prior cold native six-significant-figure volume, surface area, centroid, signed bounds and seam measurements. Circle and rectangle controls still passed. The [reader proof](../../../../../re/solidworks/records/EllipsePublicRead2026.md) documents the supported ownership and links the corresponding receipts.
