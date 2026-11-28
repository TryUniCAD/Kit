# Feature errors need a Boolean output parameter

## Expectation

`IFeature.GetErrorCode2` accepts the integer-reference helper used by document
open/save error APIs.

## Actual behavior

The installed SOLIDWORKS 2026 type library declares its `IsWarning` parameter
as an output pointer to `VT_BOOL`, with an `VT_I4` return value. The original
`VT_BYREF | VT_I4` call failed with a type mismatch for every feature in the
polygon source-authoring batch. A successful save and solid-body measurement
did not establish zero feature errors or warnings.

The [recorded type-library descriptor](../../../../re/solidworks/v2026/evidence/FeatureErrorTypeLibrary.json)
binds this declaration to SHA-256
`e71e9834f3ca4de85a321b9147c6805b34808e36a8b48149ab6a14bb41a7d6f4`.
Its argument descriptor `((26, 11), 2, None)` is a pointer to a Boolean with
the output flag. This was static metadata inspection, with no CAD application
launch or attachment.

## Workaround

Pass `VARIANT(VT_BYREF | VT_BOOL, False)` and record both the returned code
and warning value. Keep query exceptions in the evidence; do not convert them
to zero. The research harness now uses a separate Boolean-reference helper.
The original held-out source hashes remain unchanged and their lock explicitly
records the missing per-feature error evidence.

`InspectTypeLib.py` requires an absolute type-library path. The
[Windows API contract](https://learn.microsoft.com/en-us/windows/win32/api/oleauto/nf-oleauto-loadtypelib)
states that supplying the library path avoids implicit registration.
