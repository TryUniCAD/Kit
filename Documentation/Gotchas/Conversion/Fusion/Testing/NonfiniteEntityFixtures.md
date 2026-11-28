# Entity emission refuses nonfinite corruption fixtures

Changing a typed floating field to infinity and emitting a Fusion document does not create a negative reader fixture.
The existing entity encoder rejects nonfinite scalars first, so that attempt never reaches archive reading.

Emit a unique finite sentinel into the intended typed binding, resolve the validated container, and replace exactly one binary64 sentinel in its bulk streams with infinity.
Re-emit the container so ordinary archive framing and checksums remain valid, then exercise the public document reader.
This is a test corruption technique only; production emission remains finite-only.

The [qualification package](../../../../../re/Fusion/OffsetAdmission20261127/README.md) retains the initial encoder refusal and the repaired public archive checks.
