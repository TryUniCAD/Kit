# Measure generated polygons through native editing and reopening

The three prelocked polygon cases now open and rebuild as native one-solid parts,
accept a live extrusion-depth change, save cleanly and reopen with the expected
edited geometry. Both original native controls pass. All original inputs remain
unchanged, with zero native open, feature or save errors and warnings.

The [record](../../../re/solidworks/records/PolygonNativeMeasurements2026.md) and
[full report](../../../re/solidworks/measurements/2026/PolygonDepthEdits.json)
retain source locks, generated hashes, exact 2026 executable identity, remote
artifact provenance, native feature trees and every measured dimension, volume,
area and center of mass. Independent regeneration on the later PR head produces
identical output bytes. No edited native copy becomes a writer input.

This is measured research coverage of the selected straight-edge polygon and
blind-extrusion subset. It does not enable production writing or establish the
remaining feature families, configuration/assembly coverage or FCStd conversions.
