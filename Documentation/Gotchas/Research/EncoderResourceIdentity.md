# Encoder fingerprints include loaded SDK resources

The research encoder uses a checkout fingerprint to bind a candidate to the implementation that produced it.
A fingerprint based only on Python files omits resources that the implementation reads at runtime.

The SOLIDWORKS reader loads its root layout from JSON.
The Fusion reader loads the native class vocabulary from an XZ resource.
Either resource can change in a working checkout while its Python files and Git revision stay the same.
See the [SOLIDWORKS layout reader](../../../src/convert/adapters/solidworks/Config/RootLayout.py) and [Fusion vocabulary reader](../../../src/convert/Formats/Fusion/EntityCodec/Vocabulary/ReadCatalog.py).

Include those resource types and the shared research helpers in the checkout fingerprint.
Compare the fingerprint before and after the run. Discard the result if it changes.
The run also records the zlib build and runtime versions and the standard-library Zstd version used for Fusion input.
Existing artifact digests still bind the exact candidate bytes.
See the [encoder workflow](../../Changes/Research/Encoder/EncoderRoundTripPipeline.md).
