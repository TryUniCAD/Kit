# Capture the pinned framework string-map code spans

`InspectMfcRuntime.py` adds the opt-in `--capture-string-map-spans` inspection.
The existing owned x64 Python process loads the exact System32 MFC runtime,
checks its process and module architecture and resolves ordinal 12804. The
effective mapped export must match RVA `0x6bf870` and its exact fast-forward
entry must reach RVA `0x5cca60`.

The probe captures that fourteen-byte entry and five complete code spans. The
map serializer, wide string reader/writer and string-length reader/writer must
match their pinned original-file hashes. Their bounds come from the original
ARM64 exception directory and xdata or packed unwind record. Captures stay in
a new private directory outside repository checkouts. Existing controls for
source identity, mapped bounds, total capture size and owned-reference release
apply to this path.

Use this flag alongside `--capture-count-bodies` to corroborate the complete
count/string dependencies during one generic-runtime inspection. This is
code-byte inspection. It invokes no archive method, CAD application, COM API,
existing application process or service. Runtime files and earlier inspection
receipts retain their existing custody.

The new path has passed AST inspection only. Mapped capture, schema admission
and native model acceptance await their own evidence. Existing MFC RuntimeView03
already records the effective export table, while this option closes the
additional code-span equality boundary.

[Existing native framework count proof](../../../../../re/solidworks/records/MfcCountArchive2026.md)
