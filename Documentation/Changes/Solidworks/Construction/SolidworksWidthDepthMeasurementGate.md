# Restore exact native publication for a width-to-depth equation

The standalone SOLIDWORKS writer accepts the measured Front Plane
rectangle with two driving sketch distances, a fixed origin coincidence
and a forward blind boss whose depth is the local width divided by two.
The shared part constructor derives the archive from the neutral model.
Publication requires the authenticated width-to-depth report and the
complete measured archive digest.

Call `write_document` at the measured filename and encoded self locator.
Use the parsed
[width-to-depth report](../../../../re/solidworks/measurements/2026/SdkWidthDepthPreparationNative01.json)
as `values["solidworks_native_measurement"]["receipt"]`. Set the
accompanying `written_at` integer to `1795164000`. A seekable binary
stream requires the exact measured `final_destination`. A strict full
cold readback can publish through the same entry point after whole-model
comparison with its regenerated archive.

Two independent host processes regenerated the 9,157-byte archive and
all ten streams. Each process exercised seven publication routes and
eleven scoped refusals with untouched destinations. The previous native
lifecycle measured the exact archive with healthy controls and a live
width edit. The publication scope is this disclosed archive at the
recorded event and locator. [Current process receipt](../../../../re/solidworks/measurements/2026/SdkPublicWidthDepthMeasured02.json)
· [Native evidence and scope](../../../../re/solidworks/records/WidthDepthSameLocator2026.md#exact-publication-on-the-aggregate-writer)
