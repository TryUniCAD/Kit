# Sheet plane handles precede persistent IDs

An unformatted drawing sheet's sketch plane has a nonnegative persistent ID in the saved feature tree. The sketch's persisted component-plane handle still carries ID `-1`. The sheet reset creates the handle before inserting the plane and assigning that feature's persistent ID. The handle retains an inline alias to the real plane. The archive registers that same plane when it writes the ordered node list.

Generate the handle while the plane is unassigned and keep the actual object alias through later allocation. Its creation-log time uses the unset sentinel, and its unit component is an owned copy of the drawing's self component. Regenerating the handle after allocation changes the native inline reference shape. [Constructor evidence and control receipt](../../../../../../re/solidworks/records/DrawingEmptySheetObjects2026.md)
