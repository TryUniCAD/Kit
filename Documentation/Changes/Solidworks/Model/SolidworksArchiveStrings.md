# Typed native archive strings

The shared archive adds pure memory string primitives under `src/convert/adapters/solidworks/Archive/Strings`.
These primitives do not expose a SOLIDWORKS adapter writer.
Remote corpus verification passed with the shared object/map implementation on source `9d7209d515d6d7c6fafa461ae7dad917c97f8226`.

`CStringValue(TextValue, IsUnicode)` requires explicit text and source encoding.
The immutable value stores no payload, length, offset, template or saved field program.
`EncodeString(StringValue)` derives every emitted byte from that value and the documented string grammar.
Its default contract accepts Unicode output, matching the inspected native wide-string writer.
`IsSourceFrame=True` additionally preserves ANSI source frames during reconstruction of that same source document.
It does not provide a fresh ANSI semantic writer.
`ReadString(BufferValue, OffsetValue)` returns the typed value and the next offset.
Neither operation reads files or imports research, vendor or CAD runtime modules.

ANSI payloads use the existing one-byte Latin-1 mapping.
This preserves source bytes without selecting a locale code page.
Unrepresentable ANSI text fails explicitly.
Unicode payloads use UTF-16LE with `surrogatepass`.
Lengths count encoded bytes for ANSI and encoded 16-bit units for Unicode.
Non-BMP characters and lone surrogates therefore retain the existing research codec behavior.

The canonical length width is one byte below `255` and a marked word below `0xfffe`.
Larger lengths use the marked unsigned 32-bit form.
Unicode adds the separate `ff fe ff` marker before its length.
No terminator or BOM is added.
Empty ANSI and empty Unicode remain distinct values and frames.
The reader accepts unambiguous overlong length forms, while the encoder chooses canonical width.
It rejects a repeated Unicode marker and reserved double-word length `0xffffffff`.
It rejects lengths beyond the signed CString limit `0x7fffffff`.
Arbitrary noncanonical frame identity is not claimed.

Wrong value, buffer, offset or flag types raise `TypeError`.
Invalid positions, truncated headers or payloads, unsupported lengths and unrepresentable ANSI text raise `ValueError`.
The reader checks the declared payload boundary before slicing or decoding.
Offset arguments remain unchanged when decoding fails.

The implementation retains the research codec representation and canonical thresholds.
Direct 2026 inspection corrects its permissive repeated-marker and reserved-length paths.
The [recorded string grammar](../../../../re/solidworks/archive/Grammar.md#22-strings--confirmed) supplies historical framing context.
The [resolved-feature record](../../../../re/solidworks/records/Resolvedfeatures.md) distinguishes ANSI and Unicode forms.
The [2026 native archive record](../../../../re/solidworks/records/MaterialDisplayArchive2026.md) identifies the wide-string call boundaries.
The [source-admission receipt](../../../../re/solidworks/measurements/2026/CurveDiscoveryAdmissionCf26.json) covers the earlier research codec, not this draft.
The [2026 primitive record](../../../../re/solidworks/records/CStringArchive2026.md) binds complete native functions, length branches and mode gates.
No long-string oracle measurement or semantic ANSI code-page equivalence is claimed.

The research archive now routes every string read and write through these production modules.
It converts typed results to its existing Unicode text or `("A", text)` representation.
It validates ANSI tuple shape and selects source-frame reconstruction explicitly.
The focused `ReadLength` helper separates sentinel decoding from text payload decoding.
Field inventories include all four production source hashes, and their process assertions require those exact modules.

Source, AST, and Black checks passed without executing a codec, schema, or local test.
Independent original-PE inspection verified nine complete native function spans and thirteen relative-call targets.
Remote process checks must retain all 234 strict stream identities, completed phases, linked-map seeds, and retained field graphs.
The three existing negative process cases remain active.
The [complete modeled-archive check](SolidworksStringArchiveProcesses.md) passed its first remote execution on source `0b6e657648a08845ed19939dfe588b2e1c851248`, covering ten positive cases and three malformed-frame rejections.

See the [encoding and length gotcha](../../../Gotchas/Conversion/Solidworks/Archive/CStringEncodingAndLengthUnits.md).
The [CAD criteria](../../../Reference/Operations/CadSuccessCriteria.md) and [writer method](../../../../re/Playbook/WriterModel.md) still apply.

> The first is success under every criterion on this page.
> The second is the end of the available context.

This internal layer establishes no native writer or held-out model acceptance.
