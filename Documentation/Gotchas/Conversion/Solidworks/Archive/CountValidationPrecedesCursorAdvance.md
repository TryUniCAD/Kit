# Validate collection capacity before advancing the archive cursor

A complete count field can declare more items than fit in the remaining
bytes. Advancing the cursor as soon as the count decodes makes that
rejection point past the offending field. A truncated count instead leaves
the cursor at its start.

Check capacity from the decoded next offset before assigning it to the
cursor. The [bounded count reader](../../../../../src/convert/adapters/solidworks/Archive/Reading/ReadNativeCount.py)
keeps either failure positioned at the count field.
