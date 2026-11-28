# Write the scoped SOLIDWORKS width-to-depth equation

`convert.write_document` accepts a neutral Front Plane rectangular
blind boss with an explicit fixed origin datum and active corner
coincidence. Its derived depth uses `"D1@Sketch1" / 2`, with the actual
sketch name and actual width parameter ID. The existing part settings
and destination policy supply the ordinary document defaults.

The [native trial](../../../../re/solidworks/measurements/2026/SdkWidthDepthPreparationNative01.json)
passes 170 candidate checks and 18 control checks across six fresh
processes. The driving width edit changes the derived depth and both
persist through save and reopen. Two normal API processes reproduce
the exact native-tested file with zero runtime reads and strict
geometry readback. Five unsupported intents refuse before publication.

[Normal writer proof](../../../../re/solidworks/measurements/2026/SdkPublicWidthDepthWriter01.json)
· [Pre-writer-locked family evaluation](../../../../re/solidworks/measurements/2026/WidthDepthLockedEvaluationNative01.json)
