# A PE import-symbol budget can hide the unit-map owner

An import search can incorrectly report that no supplied DLL initializes the
native unit-string maps. The installed `pefile` parser defaults to a maximum
of 8,192 imported symbols. Large 2026 SOLIDWORKS modules exceed that budget.
A negative result from a truncated import directory does not establish absence.

With `pefile.MAX_IMPORT_SYMBOLS` set to 100,000, the same `sldappu.dll` exposes
`unitStrEntry` construction at IAT `0x45e518a0` and
`moLengthUserUnits_c::setUnitsStringMap` at IAT `0x45e518c0`.
Native call `0x458118e1`, in initializer `0x4580f7a0`, references the latter.

Export names have a separate 8,192-symbol budget. Pass
`max_symbol_exports=100000` to `pefile.PE` when inspecting the large format DLL;
changing the module constant after import does not change the constructor's
bound default argument. Otherwise later exported setters appear unnamed even
though their function addresses are present. The complete directory exposes
the folded balloon and button setters needed to verify their actual offsets.

Set an explicit sufficient symbol budget for static PE inspection, preserve
parser warnings and validate coverage before treating a negative import search
as evidence. This is a static analysis setting; the writer does not read a PE
file or use imported addresses at runtime. The
[construction finding](../../../../re/solidworks/records/StyleConstruction2026.md)
records the associated unit-owner investigation.
