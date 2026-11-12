# Fusion archive inspection and ZIP Zstandard

A generic ZIP inspector can recognize an F3D archive but fail to inspect its entries.
The tracked Fusion corpus declares ZIP compression method 93 for 10,537 members.

REA 6.8.0 `inspect-artifact` rejected the controlled `revolve_partial.f3d` archive with `Compression method not supported`.
The same tool inspected the DEFLATE-compressed F3Z example successfully.
Its saved evidence describes container entries and explicitly excludes Fusion-specific semantics.

Use a bounded Zstandard-capable archive reader for method 93.
Python 3.14 provides standard-library ZIP support for this compression method.
Preserve the original archive digest when recording analysis of decompressed members.
Do not treat successful container inspection as proof of feature decoding or vendor-loadable writing.

See the [saved evidence](../../../../re/Fusion/Reconstruction/ReaAssemblyEvidence.json), [inventory](../../../../re/Fusion/Reconstruction/CorpusInventory.json), and [fixture compression note](../../Ci/FusionFixtureCompression.md).
