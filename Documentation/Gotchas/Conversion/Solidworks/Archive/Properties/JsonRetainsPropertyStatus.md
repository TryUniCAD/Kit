# JSON preserves native property inspection status

An interchange JSON snapshot can retain both the original SOLIDWORKS
source identity and the diagnostic for unavailable native text. Using
the model's source format to determine which adapter read the input
can reject an otherwise lossless JSON copy.

The conversion registry uses the selected input and output adapters
for the copy decision. A registered JSON reader and JSON writer can
preserve an eligible snapshot and its original information diagnostic
when neither configuration selection nor geometry filtering is requested.
The ordinary sketch-support and native feature checks still run during
publication. A decoded native timeline can remain inspectable through
JSON while those checks refuse an export. Keep the provenance and
diagnostic with the snapshot.

The same geometry-only interchange snapshot produces identical documents
and output bytes on accepted main and the property branch. It carries
the imported solid with its original source and diagnostic. Both SDK
entry points report body structure, B-rep and configurations. The
native feature refusal, filtered copy refusal and new native output
policy still apply at their separate boundaries.
[Process cases](../../../../../../tests/Convert/Solidworks/Properties/WriteTextTests.py)
