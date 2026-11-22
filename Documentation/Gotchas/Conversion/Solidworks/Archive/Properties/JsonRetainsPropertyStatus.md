# JSON preserves native property inspection status

An interchange JSON snapshot can retain the SOLIDWORKS source identity
and the diagnostic for unavailable native text. Opening that snapshot
keeps its inspection document and original diagnostic.

The conversion registry checks the status on the root and all owned
documents. Conversion and direct publishing refuse an unavailable
property scope, including an unfiltered JSON-to-JSON request. Changing
the source format label preserves the refusal. Use document inspection
to read the snapshot and keep its provenance and diagnostic together.
[Process cases](../../../../../../tests/Convert/Solidworks/Properties/WriteTextTests.py)
