# A mass status output precedes the final input

The exact registered `IModelDocExtension.GetMassProperties2` has three positions: accuracy input, status output and `UseSelected` input. Supplying `pythoncom.Missing` for the middle output can omit the later boolean: pywin32 stops its typed positional scan at that sentinel. A guessed status or the input placeholder cannot establish native success.

Use the registered DISPID `286` and explicit type/flag descriptors `(VT_I4, FIN)`, `(VT_BYREF|VT_I4, FOUT)`, `(VT_BOOL, FIN)`. Supply all three positions with a numeric middle placeholder and `False` as the final input. Require the actual returned `(twelve_metrics, status)` pair and read status zero from that output. Keep any typed-call failure visible and verify the new binding against a pristine control before interpreting candidate measurements.

This is a source/API binding rule, not a measured claim that mass accuracy explains an oblique solid's existing mismatch. The document method's accuracy argument also has a different contract from `IMassProperty2.AccuracyLevel`. [Exact metadata, diagnostic and remaining limits](../../../../../../re/solidworks/records/ObliqueCylinderMassPrecisionProtocol2026.md) · [pywin32 typed-call implementation](https://github.com/mhammond/pywin32/blob/main/com/win32com/src/PyIDispatch.cpp)
