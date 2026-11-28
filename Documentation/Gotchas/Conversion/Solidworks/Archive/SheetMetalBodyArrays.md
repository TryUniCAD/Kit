# Sheet-metal body arrays use different child classes

A populated configuration can appear to use one shared per-body record for both sheet-metal arrays. The directly owned `f1018` master uses `n370/f358` and the legacy `moPerBodySheetMetalData_c` child. The later configuration bridge uses `n16f8/f16e8` and `moPerBodySheetMetalDataNew_c`. Their observed serializer call sequences differ. The runtime class registration schema word is not the native wire tag.

Keep both lanes and the actual module build identities separate. Use class-tag and archive-map evidence plus native body and topology controls before admitting a populated layout. [Static comparison](../../../../../re/solidworks/records/SheetMetalPerBodyStatic2026.md)
