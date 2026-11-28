# Changing standard does not reinitialize details

Changing the detail standard selector is not a complete style operation. In the pinned 2026 build, `moDetailDefs_c::setStandard` at `0x3c7dc360` stores a nonnegative argument at actual receiver `+0x10` and returns. It does not update the nested defaults, constructor `f138` or Swift owner.

The native constructor starts with standard one and initializes `f138=1`. The disclosed standard-zero source graphs also retain `f138=1`. Inferring zero for every apparently standard-related field loses that ownership distinction. The Definition's separate empty `moANSI_c` object is another owner and does not establish the model's detail selector.

Construct the complete owned graph and apply the actual standard-default operation. Preserve fields that operation does not write, and retain independent source overrides explicitly. Fonts, character spacing, nested unit records, Swift and GTol settings cannot be replaced by an observed ANSI row or by changing the selector alone.

The [exact-build ledger](../../../../../../re/solidworks/records/DrawingAnsiStyleConstruction2026.md) binds the complete native functions and the [guarded codec receipt](../../../../../../re/solidworks/measurements/2026/DrawingAnsiStyleConstruction01.json). Its new constructor operation is archive-qualified only; native and held-out qualification remain pending.
