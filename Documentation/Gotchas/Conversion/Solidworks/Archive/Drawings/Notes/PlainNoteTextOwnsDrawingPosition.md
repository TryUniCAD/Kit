# Plain note text owns its drawing position

The display item can carry an absolute attachment point even on a plain note without an external entity. In two independent notes, that attachment point differs from the position passed to the public note API. Their edited saves keep the distinction.

Follow the actual note data's generic text and read its inherited position. The attachment and display-point cache own a separate origin. The display direction uses the normalized difference between the origins. [Pinned native getters and disclosed comparisons](../../../../../../../re/solidworks/records/DrawingPlainNotePortableOwners2026.md)
