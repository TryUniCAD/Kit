# Header log text has its own representation

The `f50` key does not have one type across archive classes. `moHeader_c.f50` is a time word. `moLogs_c.f50` is the log name after its stamp collection.

Fresh `MakeRootLog` supplies that name as `CStringValue`, with explicit text and encoding. A plain nonempty datum-name accessor rejects it. Header and body readers can also expose their declared decoded text representation. Stamp comments use their own text field and can legitimately be empty.

Use the actual class/field owner and accept only its supported typed string or decoded text form in observers. Retain the underlying object and encoding for byte re-emission. Do not coerce unknown objects with `str`, change a time field, or weaken a codec to repair a reporter error.

The [epoch experiment record](../../../../../../re/solidworks/records/DrawingSourceEpochExperiment2026.md#retained-first-failure) binds the immutable failed first process and the corrected full replay.
