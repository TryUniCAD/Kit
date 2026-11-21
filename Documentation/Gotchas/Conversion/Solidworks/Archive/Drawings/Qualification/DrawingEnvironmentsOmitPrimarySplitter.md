# Drawing environments omit the primary splitter

The shared part/assembly `uiUserModelEnv_c` layout includes two embedded splitters. Reusing it unchanged for a drawing would consume the following presentation words as the first splitter header and misalign the stream.

The exact native serializer checks the owning `SldModelContext_c` for part or assembly in both read and store branches. The bound ordinary drawing document returns false for both, so its first `f10` splitter is absent. Its secondary `fe0` splitter, including every nested header word and cell, is still serialized.

Use the drawing-only rule under the existing ordinary drawing context guard. Exclude only the direct environment `f10` operation; do not remove nested splitter `f10`, substitute an empty first splitter, or alter shared part/assembly grammar. Unknown substituted contexts remain outside this scoped profile.

The [native environment proof](../../../../../../../re/solidworks/records/DrawingUserEnvironmentArchive2026.md) binds the actual helper, context predicates, UI document dispatch, complete serializer, and embedded splitter owner to the installed build.
