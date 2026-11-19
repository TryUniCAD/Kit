# Attached note depth uses its attachment plane

An edge-attached drawing note accepted `SetPosition2(x,y,0)` but returned nonzero Z. X/Y matched exactly. Native code explains the restriction: the ordinary note setter transforms its offset from the actual attachment into the note frame and, under its planar predicate, forces the local normal component to zero. Requested sheet Z therefore need not become the returned note Z.

Keep requested, constrained and returned coordinates separate. For the bounded canonical Front cap probe, compute the constant projected attachment depth using both real edge endpoints and the independently checked view transform, retaining its translation and scale separately. Do not replace zero with a fitted half-depth or ignore Z. Test opposite requested-Z offsets while retaining exact X/Y and full attachment/save/reopen checks.

The full attachment-cache/view-frame rule remains a declared hypothesis until controlled independent geometry passes. Rotation-only `GetPlane` has no translation origin, and the COM note origin is not an archive text-point field. [Pinned source, preserved failure and frozen retry](../../../../../../re/solidworks/records/DrawingAttachedNoteDepth2026.md)
