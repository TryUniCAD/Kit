# A displayed circle centre can move by one binary64 step

The disclosed Front-plane diameter circle reads its centre from the actual
typed point. Its public Y coordinate is `-5.675000000000001` mm because the
reader projects the metre word with a multiplication by 1,000. Writing
that displayed value shifts the native word by one binary64 step. The
authored `-5.675` mm and the recorded metre word can be paired exactly
using the inverse of the writer's `0.001` coefficient.

For cold republication, check that the public centre agrees with the typed
metre word and reconstruct an exact inverse. Use the separately bound
radial driver to reconstruct the radius. Compare the complete strict
readback of the new archive and require its original measurement before
publishing.

[Circle republication evidence](../../../../../../re/solidworks/measurements/2026/SdkMeasuredCircleRepub01.json)
