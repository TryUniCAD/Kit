# Recheck the paired rectangular native measurements

The [guest-only recheck](../../../../../re/solidworks/records/SdkSealedBareRectangleReadjudication2026.md)
verifies the existing native phase records and both saved derivatives.
It compares the original and generated mass properties at six
significant figures and applies the prescribed absolute tolerance
near zero. It reuses the original native measurements and runs a
guarded strict SDK read on each candidate and separate save.

The original failed receipt remains available. The recheck publishes a
separate result and starts no CAD process.
