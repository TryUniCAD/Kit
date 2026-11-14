# SOLIDWORKS archive fixture editing

## Expectation

Replacing a depth label inside a self-generated `.SLDPRT`'s raw bytes is a valid way to emulate a vendor-authored rounded label for a regression case.

## Actual behavior

Native streams contain compressed data, checksums, sizes, and directory offsets. Byte-sequence replacement searches the container instead of the decoded label, so it can fail to find anything or invalidate multiple fields. One regression failed before native depth recovery could execute.

Whole-container replacements also make arbitrary archive bytes into an invalid test fixture. Changing only the replacement length does not address that structural problem.

## Workaround

Open the native archive, decode the keyword stream, edit only the intended `Dimension` element through the untrusted-XML parser, and serialize it with the original pre-XML prefix retained. Rebuild using `BuildSldprt` with the original input archive as the container template so its stream records, signatures, sizes, and checksums are recomputed. The source document's own streams may be used for this source-specific metadata case; they are not a production donor template.

Self-generated files also contain `Kit/Interchange`. Public `open_document` intentionally returns that embedded neutral document before native decoding. A regression intended to exercise native depth recovery must omit `Kit/Interchange` and its matching `Kit/Native` attestation from the edited fixture. Otherwise a valid archive and a correct depth guard can both be present while the assertion measures only the embedded copy.

Use changed typed fields such as the resolved depth witness only where an invalid-input guard needs to be exercised. Generate valid compressed containers through the same helper for every such case, then use `open_document` for acceptance. Promotion into production still requires the independently recovered grammar rather than this test-fixture utility.

See [BuildSldprt](../../../../src/convert/adapters/solidworks/container/Container.py), [the corrected integration coverage](../../../../tests/convert/solidworks/resolved/SolidworksPolylineThreeTests.py), and [the native depth gotcha](SolidworksTriangleDepthRecovery.md).
