# Truncated vtable inventories need direct slot reads

A bounded vtable inventory can stop before a slot that the native code actually calls. The private 2026 model-format inventory describes `moLinearDimDef_c` at `0x3cc6c278` with forty displayed slots. The complete base-dimension default function also calls actual slot `+0x140`, whose index is forty.

Reading the original pinned PE independently resolves that cell to `0x3c798640`. Its complete seven-byte body stores the integer argument at the actual linear receiver's `+0x104`. The ANSI branch supplies zero. Treating the inventory's displayed count as the native table boundary would miss this owned mutation.

Validate an actually reached slot against the original module, concrete RTTI, constructor-installed vtable and complete target body. Retain bounded-inventory limits separately from native class layout. Do not extend a table by guessing from adjacent pointers.

The [ANSI native record](../../../../../../re/solidworks/records/DrawingAnsiStyleNative2026.json) binds the module SHA, cell hash, constructor and target body. This is static dispatch evidence; it does not claim the function was observed executing.
