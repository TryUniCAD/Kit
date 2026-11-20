# SOLIDWORKS KeyWords XML framing

`FrameKeywords` encodes an ordinary `Keywords` element tree as
UTF-8. It adds the native stream marker, XML declaration and CRLF
framing. The caller selects compact or space-padded empty tags
explicitly. Ordinary attributes, text and child tails retain their
characters through XML escaping. Numeric character references preserve
CR and CRLF through XML end-of-line normalization.
[Carriage-return handling](../../../Gotchas/Conversion/Solidworks/Archive/Metadata/KeywordTextPreservesCarriageReturns.md)

The framing contract covers named elements, attributes, text and child tails. A nonempty root tail refuses before serialization.
Comment and processing-instruction nodes fall outside that vocabulary.
Configuration and feature projection follow their own format rules.

The [authored process](../../../../tests/Convert/Solidworks/KeywordFrames/KeywordModelTests.py)
compares independent bytes and reads back the authored values. The
[disclosed process](../../../../tests/Convert/Solidworks/KeywordFrames/KeywordSourceTests.py)
checks exact re-emission of compact and spaced controls. The
[refusal process](../../../../tests/Convert/Solidworks/KeywordFrames/KeywordRejectTests.py)
checks the root and formatting arguments. These process checks await
remote CI.
[Source and format evidence](../../../../re/solidworks/records/KeywordFrameSlice2026.md)
