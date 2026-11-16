# Line-style names resolve by an ordered prefix search

An explicit dimension line-style name cannot be converted to a native display index using an exact-name dictionary lookup.

The pinned SOLIDWORKS 2026 `sldmfcu.dll!apLineStyleMgr_c::getLineIndex` at `[0x3c849620,0x3c8496cc)` scans the manager's list in order, skips null entries, obtains each internal name, and compares only the query's UTF-16 code-unit length through imported `_wcsnicmp`. The first match supplies the index. No match returns `-1`; the display initializer then retains its prior index. An empty query selects the first nonnull row.

For radial displays the caller is `sldmodu.dll!moDisplayItem_c::initLeaderFrameStyleAndWidth` at `[0x4ba6cb60,0x4ba6cd3e)`. It obtains the catalog through `SldSession_c::Environment()` and that receiver's virtual `+0x1f8`. Leader and extension lookups write display `f308` and `f31c`; widths are separately copied to `f30c` and `f320`, even when name resolution fails.

A pure constructor needs a proven ordered catalog and supported comparator domain. A saved index, an exact-match map, Python code-point length or unrestricted Unicode `casefold` is not a demonstrated replacement for the native operation. The normal session wrapper and conditional active-document/environment selection are now bound in the [style/engine record](../../../../../re/solidworks/records/RadialStyleAndEngine2026.md); actual runtime overrides and portable pattern semantics remain separate. This lookup proof supplies no resolver default or accepted writer.

Evidence: the [style evidence](../../../../../re/solidworks/records/RadialStyleConstruction2026.json) and [construction record](../../../../../re/solidworks/records/RadialStyleAndEngine2026.md). Original model module SHA-256 is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`; MFC module SHA-256 is `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`. Verification was bounded static PE/LLVM inspection only; no native execution or acceptance occurred.
