# Child display selection has its own state key

In six disclosed native concentric parents, the insertion options
have an empty display name and key `-1`. Each actual occurrence's
separate CMgr row selects the child's display state by name and
key, with the display-override bit set. Both values resolve through
the child's actual selected configuration in its own VisualStates
store.

Derive the occurrence selection from the actual referenced child.
Match its name and key in the child's own state map before encoding
the presence bit.
[Source and generation evidence](../../../../../../re/solidworks/records/ConcentricSavedCmgrModel2026.md)
