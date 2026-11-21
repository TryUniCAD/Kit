# Reconstruct a cache-free SOLIDWORKS width-to-depth part

The strict default part reader reconstructs the measured version-19000
Front Plane rectangular blind boss when its native Parasolid cache is
absent and one authenticated local depth equation uses half the live
sketch width. It uses the proven configuration and resolved map from
the equation reader, then applies the ordinary prism and body checks.

The [host proof](../../../../../re/solidworks/measurements/2026/SdkColdWidthDepthGeometry01.json)
matches the disclosed generated reference and plain parts in topology,
volume, area and centre of mass. The two native-saved controls retain
their three native payloads. Nine faults, including an altered archive
prefix, cloned handle, evaluated depth and cached value, refuse strict
reconstruction. The resulting neutral geometry has no native payload.
