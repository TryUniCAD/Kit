# JSON preserves native property inspection status

An interchange JSON snapshot can retain both the original SOLIDWORKS
source identity and the diagnostic for unavailable native text. Using
the model's source format to determine which adapter read the input
can reject an otherwise lossless JSON copy.

The conversion registry uses the selected input and output adapters
for the copy decision. A registered JSON reader and JSON writer can
preserve the snapshot and original information diagnostic when neither
configuration selection nor geometry filtering is requested. The CLI
also applies its existing checks for opaque native records.
Keep the source provenance and diagnostic with the snapshot.
[Process cases](../../../../../../tests/Convert/Solidworks/Properties/WriteTextTests.py)
