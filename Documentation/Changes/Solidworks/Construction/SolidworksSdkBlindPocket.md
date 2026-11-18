# Construct a blind pocket from neutral part history

The internal SOLIDWORKS 2026 SDK composer builds a complete part with a rectangular blind boss followed by a reversed blind circular cut. Both sketches use the actual Front Plane owner. The cut keeps its own editable depth and follows the supplied circle sketch, including a fixed-centre radius, a fixed-centre diameter or an undimensioned circle.

The builder allocates both features and derives Config-0, ResolvedFeatures, KeyWords and the rest of the container through the shared codecs. It checks the single-solid dependency, radial clearance and cut depth before allocating native objects.

Run the build worker with a portable document request on standard input.

```sh
python -I -B re/tooling/sw2026/SdkPocketProcess.py "$PWD" build < REQUEST.json
```

The disclosed fixture author is `re/tooling/sw2026/AuthorSdkPocketInputs.py`. Seventeen fresh processes verify deterministic builds, 30 exact stream comparisons, six admission rejections and zero runtime file reads. Adding the cut increases the resolved topology and byte length in every design. [Construction rules](../../../../re/solidworks/records/SdkBlindPocket2026.md) [Process measurements](../../../../re/solidworks/measurements/2026/SdkBlindPocketProcess01.json)

All three generated parts open with one solid and zero errors or warnings in SOLIDWORKS 2026 SP05.2. The cut depth edits and the radius and diameter edits rebuild successfully. All three saves reopen with their original feature tree, and their six linked SDK archive streams re-emit exactly. The native batch passes 275 checks in 12 fresh processes with six healthy controls. Held-out comparison and public writer admission remain open. [Native measurements](../../../../re/solidworks/measurements/2026/SdkBlindPocketNative01.json)
