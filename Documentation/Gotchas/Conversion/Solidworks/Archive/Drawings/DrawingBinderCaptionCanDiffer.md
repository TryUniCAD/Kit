# The drawing binder caption can differ from its archived name

The ordinary SDK blank drawing retained the authored binder name in the
typed `moDocsFolder_c` node. SOLIDWORKS 2026 SP05.2 displayed `Design Binder`
through the native feature API. The other nine tree rows and all eight
sheet property values matched the authored prediction. A whole-tree
comparison caught the caption difference before the edit.

Measure the persisted name and the native displayed caption separately.
The ordinary English blank trial uses the standard binder caption and
requires all ten tree rows, including the binder, to match across edit,
save and reopen. [Native comparison and failed control variant](../../../../../../re/solidworks/measurements/2026/SdkBlankDrawingNative01.json)
