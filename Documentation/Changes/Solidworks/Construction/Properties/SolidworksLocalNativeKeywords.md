# SOLIDWORKS local import native keyword index

The local-part constructor accepts an explicit keyword title, time and
unassigned configuration material label. It indexes actual feature
roots, the environment lights, the note members and the optional empty
part exploded-view manager. The index uses native role names and sorts
by tag then decimal identifier text. The part and self-file names
continue to follow the output document.

The strict local geometry reader checks the raw index against the typed
Config-0 and resolved graph before using an import identification. The
existing class-name index remains available to earlier writer profiles.
Three disclosed cases generate all 25 native-role rows, and a separate
case with no manager generates 24 rows. The only stream that changes at
the same locator is KeyWords. Eighteen malformed cases refuse, and the
guarded generation reads zero files.

The disclosed comparison tool accepts `--native-keyword-index` when
freezing its native lifecycle.

[Model and process evidence](../../../../../re/solidworks/records/ImportedNativeKeywordIndex2026.md)
· [Raw owner binding](../../../../Gotchas/Conversion/Solidworks/Model/Presentation/KeywordIdsPrecedeNameRebinding.md)
