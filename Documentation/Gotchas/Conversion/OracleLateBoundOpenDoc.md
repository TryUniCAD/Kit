# Late-bound OpenDoc evidence

## Expectation

A VBScript call to `OpenDoc6` should be interchangeable with the compiled oracle's `OpenDoc6` call when the same arguments and explicit numeric types are used. Its returned error variables could then supply zero-load-error evidence for every corpus case.

## Actual behavior

The Parallels SOLIDWORKS 2026 installation rejected the late-bound call with VB error 13, `Type mismatch`, even after `CLng` conversion. The compiled `OpenDoc6` diagnostics executable accepted the same generated part with zero errors and correct rebuild and mass measurements. Late-bound `OpenDoc` works for feature inspection, but does not provide the `OpenDoc6` load-error outputs.

An unsuccessful call can also leave the document variable as a non-object value. VBScript's non-short-circuit `Or` then makes `ModelDoc Is Nothing` itself fail with `Object required`. Stub error strings or hardcoded zero values would fabricate evidence and are not acceptable.

A valid invocation can outlast a 120-second parent timeout and then finish, leaving the diagnostic process alive after its caller exits. Case 7 subsequently passed with exact geometry when rerun directly with a 300-second window and a measured zero-document recovery check. A missing or empty response is not evidence of an invalid file, and a sudden exit must not terminate the user's SOLIDWORKS process.

## Workaround

Use the compiled `OracleLoadDiagnostics.exe` path for actual load errors, rebuild state, body count, volume, area, depth, and centre of mass. Use late-bound `OpenDoc` only for `Sketch1`, `Boss-Extrude1`, and sketch-segment evidence. Record the open method instead of claiming unsupported error variables.

Capture `Err.Number` before leaving `On Error Resume Next`, and test `IsObject` before using `Is Nothing`. Permit one bounded retry only for a separately identified `PrlJob_GetResult` or `PrlJob_GetRetCode` transport failure, never for an invalid model result. Preserve successful case results and resume after them instead of needlessly reopening the entire corpus.

See [the compiled corpus verifier](../../../../re/tooling/harness/VerifyRandomOracle.py), [the late-bound feature harness](../../../../re/tooling/harness/OracleRandomTriangles.vbs), and [the isolated oracle path rules](OracleWorktreeSharePaths.md).
