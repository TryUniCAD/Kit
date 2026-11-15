# Generated wrappers need raw dispatch pointers

## Expectation

A generated pywin32 interface wrapper could appear to accept an existing dynamic dispatch wrapper directly.

## Observed behavior

The installed generated-wrapper base constructor unwraps generated wrappers and accepts raw dispatch objects.
It does not unwrap the dynamic wrapper returned by the oracle's untyped calls.
Passing that dynamic wrapper stores it as the supposed low-level COM object.
Later calls fail on missing `Invoke` or `InvokeTypes` members.

The rectangle and circle source controls reached those failures after explicit library loading succeeded.
The failure does not establish missing native line, arc or feature support.

## Workaround

Extract the dynamic wrapper's `_oleobj_` pointer.
Query the exact interface ID through that pointer and require the query to succeed.
Pass the returned raw dispatch pointer to the generated interface wrapper.
Record the requested interface ID with the native call.

The [explicit-interface change](../../../../Changes/Solidworks/Inspection/SolidworksExplicitOracleInterfaces.md)
records the tool behavior and its remaining verification limits.
