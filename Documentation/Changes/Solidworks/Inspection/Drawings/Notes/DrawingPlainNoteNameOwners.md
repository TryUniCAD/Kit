# Plain drawing note name owners

PR #121 records the exact SOLIDWORKS 2026 registered note-name consumer and ordinary commit allocation paths. `IAnnotation.GetName` and `INote.GetName` resolve the actual modeled note name through its `f18.f08` holder. The separately persisted node `f20` string and separately allocated display `f58` identifier retain their own meanings.

Use the [source ledger](../../../../../../re/solidworks/records/DrawingPlainNoteNameOwners2026.md) when constructing or diagnosing one ordinary unattached drawing note. It records the empty-name/detail-folder/model guard and real name-manager fallback. It deliberately leaves the localized basename, complete unusual-name scan semantics and native placement qualification open.

The [sanitized receipt](../../../../../../re/solidworks/measurements/2026/DrawingPlainNoteNameSource01.json) binds three original modules, 29 whole functions, six decoded ranges, ten imports and 13 table cells. No SDK behavior, public admission or writer qualification changes. No CAD application, VM, SDK codec, tests or saved CAD payload was used by this source task. The [owner distinction gotcha](../../../../../Gotchas/Conversion/Solidworks/Archive/Drawings/Notes/NoteNameHolderIsSeparateFromDisplayId.md) records the superseded assumption.
