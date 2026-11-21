# Native save adds a drawing system-scale row

Six fresh generated Front and Top drawings contain 16 entries in the drawing's units table. All 24 measured native-saved states contain those entries plus a schema-one `moScaleSysScale_c` object. The archive stores its type tag and no body fields. The view ratio belongs to the actual view.

Retain the row and its archive identity when reading a save. Fresh generation for the measured profiles can omit it. The comparator uses the actual field and class instead of a stored archive slot. [Exact source and save comparison](../../../../../../re/solidworks/measurements/2026/DrawingSystemScaleOwners01.json)
