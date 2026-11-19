# SOLIDWORKS drawing system-scale ownership

The 2026 SP05.2 investigation binds the empty `moScaleSysScale_c` record to the drawing's units table. The factory initializes a memory-only scale enum. The named-view scale still comes from the view's own fields.

Read the [archive owner and save comparison](../../../../../../re/solidworks/records/ScaleSystemArchive2026.md#units-table-owner-and-native-save) when updating named-view parsing or construction. The [measurement](../../../../../../re/solidworks/measurements/2026/DrawingSystemScaleOwners01.json) records 34 exact Definition read/store comparisons. The two disclosed original drawings and all 24 vendor-saved states carry the entry. The eight fresh generated states omit it. The six fresh lifecycle inputs preserve their measured view scales through native save and reopen.
