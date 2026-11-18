# Construct a blind pocket from neutral part history

The internal SOLIDWORKS 2026 SDK composer builds a complete part with a rectangular blind boss followed by a reversed blind circular cut. Both sketches use the actual Front Plane owner. The cut keeps its own editable depth and follows the supplied circle sketch, including a fixed-centre radius, a fixed-centre diameter or an undimensioned circle.

The builder allocates both features and derives Config-0, ResolvedFeatures, KeyWords and the rest of the container through the shared codecs. It checks the single-solid dependency, radial clearance and cut depth before allocating native objects.

Run the build worker with a portable document request on standard input.

```sh
python -I -B re/tooling/sw2026/SdkPocketProcess.py "$PWD" build < REQUEST.json
```

The disclosed fixture author is `re/tooling/sw2026/AuthorSdkPocketInputs.py`. Seventeen fresh processes verify deterministic builds, 30 exact stream comparisons, six admission rejections and zero runtime file reads. Adding the cut increases the resolved topology and byte length in every design. Native lifecycle and held-out qualification remain open. [Construction rules](../../../../re/solidworks/records/SdkBlindPocket2026.md) [Process measurements](../../../../re/solidworks/measurements/2026/SdkBlindPocketProcess01.json)
