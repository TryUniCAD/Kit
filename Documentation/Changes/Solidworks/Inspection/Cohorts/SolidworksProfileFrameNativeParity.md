# Verify stored principal sketch frames in native SOLIDWORKS

Two independently authored circle bosses were locked before the transform
correction. The [frozen process receipt](../../../../../re/solidworks/measurements/2026/FrameHeldoutProcesses34a.json)
verified the emitted transforms before native source access. A separate
[paired 2026 inspection](../../../../../re/solidworks/measurements/2026/FrameParityInspection01.json)
then measured the resulting Top and Right parts and their original references.

All 12 source and candidate phases opened without errors or warnings and
retained one visible solid. The 44 native sketch transform comparisons
matched all 572 stored values, including before explicit rebuild, after both
driving edits, after save and on fresh reopen. The comparison also passed 840
numeric checks, 440 exact view values and 22 ordered trees of 25 nodes.
All 50 paired volume, area and centre of mass values matched at six significant
figures. One Right-plane edited volume differed in its last binary bit.

Both controls passed and all 14 launches had distinct process identities.
Inputs and licensing processes were unchanged. This establishes the corrected
principal frame behavior for those generated research parts. It adds no
production adapter support, arbitrary-plane coverage or FCStd conversions.
