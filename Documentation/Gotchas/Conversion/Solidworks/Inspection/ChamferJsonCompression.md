# Chamfer JSON can preserve a source across different compression

The measured chamfer's original SHA-256 identifies its entire container
including compression. Equivalent DEFLATE encodings can change that SHA-256
while preserving every inflated stream and every modeled record. The
portable document has both a source member and a metadata copy of the
original digest.

The JSON writer authenticates the supplied attachment against the original
digest and compares every logical stream before verifying the complete
typed readback. It validates the generated local records, directory and
trailer so the scanner cannot leave unaccounted bytes. A byte-free snapshot
uses exact whole-file regeneration or
its independently pinned measured logical bundle to prove the original
source digest. Both digest fields remain in the output. The native writer
requires the exact measured whole file before publication.

[Disclosed compression contrast](../../../../../re/solidworks/records/ChamferDistanceMain2026.md#json-compression-boundary)
