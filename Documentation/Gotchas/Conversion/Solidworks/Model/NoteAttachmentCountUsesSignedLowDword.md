# Note attachment counts use signed low32

The `moNoteDataHelper_c` attachment count is encoded as u64. Treating that width as the native loop's integer domain is incorrect.

## Expectation and actual behavior

The provisional schema read u64 `n248`, then repeated rows only when the complete value was below `0x80000000`. Native SOLIDWORKS 2026 SP05.2 instead reads the u64 at `sldmfcu!0x3c85f512` and compares only its low32 as a signed integer at `0x3c85f51b` and `0x3c85f642`. Nonpositive signed low32 consumes no rows. Positive signed low32 consumes that many key/kind rows, with an object reference only for kinds 1, 2 and 4.

For example, `0x100000001` has native repetition count one. The previous complete-u64 comparison yielded zero. `0x100000000` yields zero, and `0x180000000` also yields zero because its low32 is negative as an i32. These are arithmetic consequences of the native instructions, not observed saved-document values or an oracle acceptance result.

## Workaround and evidence

Preserve the entire u64 wire field and compute repetitions as `low = n248 & 0xffffffff; low if low < 0x80000000 else 0`. Do not replace the source count with a normalized value or discard its high32. Keep `n248`, `f248`, `key`, `kind` and `value` key spellings and the shared 10,000,000-item safety limit.

The [native field record](../../../../../re/solidworks/records/AnnotationArchive2026.json) binds the function, instruction witnesses and surrounding grammar to `sldmfcu.dll` SHA-256 `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`. The [annotation finding](../../../../../re/solidworks/records/AnnotationArchive2026.md#note-attachment-count) and [change entry](../../../../Changes/Solidworks/Model/SolidworksAnnotationArchiveOwners.md) describe the new current-version schema.

This establishes a static parser boundary. It does not claim that SOLIDWORKS authors such high32 counts, that a large count is safe or useful, or that Kit output has passed native acceptance. Runtime vendor save canonicalization and generative count derivation remain separate work.
