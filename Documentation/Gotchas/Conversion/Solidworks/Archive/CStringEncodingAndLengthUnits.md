# CString encoding and length units are independent state

## Expectation

A decoded string alone preserves its native representation.
Its Python character count can supply the native length.
The archive collection count codec can write that length.

## Actual behavior

The existing research codec preserves ANSI as a tagged text value and Unicode as plain text.
Empty ANSI uses `00`, while empty Unicode uses `ff fe ff 00`.
Dropping the encoding choice changes those bytes even when both texts are empty.

ANSI maps each source byte through Latin-1 without choosing a locale code page.
Unicode uses UTF-16LE and `surrogatepass`.
Its length counts encoded 16-bit units rather than Python characters.
A non-BMP scalar needs two units, and a lone surrogate must remain encodable.

The string header has its own one-byte, word and double-word grammar.
The word `0xfffe` is the outer Unicode marker.
The inspected 2026 wide writer selects the double-word length at that boundary.
The vendor/framework collection count operations have different markers and thresholds.
They cannot supply CString lengths.

The reader accepts some overlong lengths which canonical storage can shorten.
Preserving text and source encoding does not preserve an arbitrary noncanonical header width.
The native reader calls one length helper twice and rejects a second Unicode sentinel.
The old research decoder instead treated inner `ff fe ff` as a literal length of `65534`.
An extended `0xffffffff` result also collides with that sentinel.
The corrected strict codec rejects both ambiguous forms before payload decoding.

## Workaround

Retain an explicit encoding flag in the typed string value.
Derive the payload and length from the supplied text during encoding.
Use `surrogatepass` for both UTF-16LE directions.
Check the complete payload boundary before slicing or decoding.
Keep the CString grammar separate from the collection count codecs.
Record actual corpus observations before claiming coverage of long or unusual string values.

This finding comes from static inspection of the existing research methods and the exact 2026 `swccu.dll` implementations.
The [native primitive record](../../../../../re/solidworks/records/CStringArchive2026.md) binds the complete functions and original module hash.
No codec, test, native CAD file or CAD session ran in this worker.
See the [string change entry](../../../../Changes/Solidworks/Model/SolidworksArchiveStrings.md),
[recorded grammar](../../../../../re/solidworks/archive/Grammar.md#22-strings--confirmed),
and [count-family distinction](FrameworkAndVendorArchiveCountsDiffer.md).
