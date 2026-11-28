# Attached drawing-note normal-coordinate probe

PR #121 adds an exact-build getter/setter pin and a narrow observer retry for an attached note whose accepted Z=0 request returned nonzero depth. Native code binds the conditional local-normal clamp relative to the actual attachment. The complete attachment-to-view provenance remains explicit unfinished work.

The new probe preserves original text, X/Y and requested Z fields, computes a separate expected depth from both selected cap endpoints and the full checked Front transform, and adds positive/negative Z-only requests. Existing correspondence, native edge/body identity, persistence, edit, save and fresh-reopen gates remain mandatory.

Two fifteen-function source pins matched exactly. In six native processes, the two bracketed controls and the generated linked pair preserve the computed note depth and persistent edge through edit, save and reopen. SOLIDWORKS adds each note after open. Generated note encoding and cache consumption remain open. [Evidence and source boundaries](../../../../../../re/solidworks/records/DrawingAttachedNoteDepth2026.md) · [Coordinate-owner gotcha](../../../../../Gotchas/Conversion/Solidworks/Oracle/Drawings/AttachedNoteDepthUsesItsAttachmentPlane.md)
