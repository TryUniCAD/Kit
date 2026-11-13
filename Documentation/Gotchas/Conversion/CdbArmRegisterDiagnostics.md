# ARM64EC debugger diagnostics

## Expectation

A WinDbg breakpoint that works for native x64 SOLIDWORKS reader calls should also support an exception breakpoint with `@rcx`, `@rdx`, `@r8`, and `kp` after `AfxThrowFileException`.

## Actual behavior

On this SOLIDWORKS 2026 Parallels installation, the breakpoint reaches `mfc140u!AfxThrowFileException`, but the combined register/`kp` command reports `EX Bad register error`. The debugger then exits and the oracle returns a negative status instead of useful file-format evidence. This can be mistaken for another native document defect or for valid exception evidence.

## Workaround

Use a supported command form and verify it independently of document correctness. On this installation, `kc` can stall during stack unwinding. Preserve a minidump, then use the debugger's `r` command for an immediate register read if that is the evidence needed. The file-exception register read returned `x0=1`, `x1=-1`, and `x2=0`. Microsoft documents cause 1 as `genericException`, not `fileNotFound` or `endOfFile`.

The initial combined diagnostic failed and supplied no valid stack evidence. Capture useful exception context before changing serialization, and do not infer a document format fault from a failed trace recipe.

See [the working object-trace commands](../../re/tooling/windbg/Traces/EnvelopeFields.txt).
