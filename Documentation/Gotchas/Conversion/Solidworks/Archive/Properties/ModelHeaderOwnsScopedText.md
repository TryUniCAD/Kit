# The ModelHeader owns the saved configuration name

A physically linked version-19000 ModelHeader can name a different
configuration from the active saved directory row. Its self file stores
the configuration name in `refcfg.f08`. The complete link resolves the
self file object and still permits its text to differ from the directory.

Before exposing configuration-scoped text, match the self file's
configuration name to the active saved directory row and the SDK
document. Keep diagnostic inspection available on a conflict.
File-level summary and custom text retain their independent scope when
there is no configuration property stream.

[Measured owner contrast](../../../../../../re/solidworks/records/LiteralPartTextReaderSlice2026.md#physical-owner-contrasts)
