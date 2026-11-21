# Folded style setters share misleading decompiler names

The compiler merges identical small setters from unrelated classes. A
decompiler can then label a call with a different exported alias and infer the
wrong receiver type or omit an argument. The surviving symbol name is not the
field's semantic owner.

In 2026 `sldmfcu.dll`, address `0x3c751c40` is exported as both
`moDimDefs_c::setArrowHeight` and `moDetailDefs_c::setCLDistance`. Its actual
instruction writes a double at receiver offset `0x08`. A call on a detail-root
receiver therefore updates centerline distance, not a dimension child's arrow
height. Several style default rules use such folded helpers.

The root constructor also passes `int(standard != 0)` in `edx` to helper
`0x3c7db840` at call site `0x3c7d1852`; the decompiler shows only one argument.
The helper writes that value to the embedded Swift object's `f3dc`.

Resolve the receiver at the call site, inspect the actual field write and check
argument registers before translating a style rule. The
[construction finding](../../../../re/solidworks/records/StyleConstruction2026.md)
records the constructor and serializer ownership. Do not fill missing arguments
or fields with a value copied from a saved part.
