# Derived handle vtables need RTTI identity

## Expectation

The constructor label or a nearby exported symbol identifies the concrete handle
whose virtual methods run after construction.

## Actual behavior

The retained SOLIDWORKS 2026 radial-handle constructor at `0x4c83d4a0` installs
vtable `0x4d242c18` at `0x4c83d520`. Direct RTTI identifies that table as
`moSkDimHandleRadial_c`, with immediate parent `moSkDimHandleValG1_c`.
The earlier radial presentation and parameter findings used the base ValG1 name
for that concrete table.

The complete-object locator is `0x4d3727d0`. Its 24-byte SHA-256 is
`6625165bfdf4d176089ba0ff0490758dbcf0ac79ad895cd91fff99dae08b9ec4`.
Its seven-entry hierarchy places radial, ValG1, sketch-handle, common
dimension-handle, component-reference, `su_CObject` and `CObject` subobjects at
primary displacement zero.
All addresses are preferred addresses in `sldmodu.dll`, base `0x4b140000`,
SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.

The actual `+0x4b8` and `+0x730` targets remain `0x4c844ab0` and `0x4c8460f0`.
The existing shared codec already has the correct radial-to-ValG1 parent link.
The correction updates the findings' concrete class label and preserves their
verified inherited-dispatch facts.

## Workaround

Read the constructor's final table assignment, that table's complete-object
locator and the actual base descriptors. Use the concrete table to resolve every
virtual call, even when its implementation is inherited.
Keep constructor aliases, semantic handle role and concrete runtime identity
separate.

The corrected [presentation record](../../../../../re/solidworks/records/RadialPresentationConstruction2026.md)
and [parameter lifecycle record](../../../../../re/solidworks/records/RadialParameterLifecycle2026.md)
retain their static scope. No new writer or native curve acceptance follows.
