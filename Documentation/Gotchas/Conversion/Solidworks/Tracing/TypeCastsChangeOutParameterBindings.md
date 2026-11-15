# Keep explicit COM out variants on an untyped call

## Expected

Explicit `VT_BYREF` variants continue to work through the same method wrapper
after a sketch or segment is cast to another COM interface.

## Actual

The primary
[pywin32 client implementation](https://github.com/mhammond/pywin32/blob/main/com/win32com/client/__init__.py)
shows that `CastTo` can generate type-library wrappers. Subsequent dispatches
can use those generated classes. Typed calls convert scalar arguments using
their declared types and return out values in the result tuple. An explicit
variant intended for untyped `Invoke` is not the scalar input expected by that
typed conversion.

The relevant conversion and returned-out-argument logic is in
[oleargs.cpp](https://github.com/mhammond/pywin32/blob/main/com/win32com/src/oleargs.cpp)
and [PyIDispatch.cpp](https://github.com/mhammond/pywin32/blob/main/com/win32com/src/PyIDispatch.cpp).
This is a source-backed binding hazard found during the curve authoring audit.
The initial native preflight did not reach these calls; no native failure or
successful corrected batch is inferred from this static evidence.

## Workaround

Use `win32com.client.dynamic.DumbDispatch` on the existing interface for calls
that deliberately pass explicit by-reference variants. It suppresses type-info
argument conversion for that call. Explicitly flag the named member as a method
before lookup, so lookup cannot accidentally perform a zero-argument property
call. The shared oracle wrapper applies this to
`OpenDoc6`, extension `SaveAs3`, and feature `GetErrorCode2`. Read each returned
status and each variant's actual value. Do not use the truth value of a tuple
as a save-success result.

The curve authoring wrapper uses the same explicit untyped method helper for
all calls with arguments. This also preserves deliberate null-interface
variants in `SelectByID2` and `Select4` after casts. It records the receiver's
wrapper class and selected binding convention with those calls.

Alternatively use generated typed signatures consistently and explicitly
unpack their returned outputs. Do not combine the two binding conventions.
Neither convention proves native geometry or file acceptance without a
controlled oracle run.
