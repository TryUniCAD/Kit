# A host architecture string does not identify the Python extension ABI

## Expectation

If `platform.machine()` returns ARM64, a Windows ARM64 Python extension can be
loaded into that interpreter.

## Actual behavior

In the 2026 SOLIDWORKS tracing VM, Python reported ARM64 and a 64-bit pointer
size. Its executable PE header was machine `0x8664` and its compiler identified
AMD64. Loading a Frida ARM64 `.pyd` failed with Windows error 193 before any
target attachment. The underlying OS, interpreter and CAD process can have
different architecture identities under emulation.

## Workaround

Read the PE machine of the interpreter and extension before choosing a wheel.
Record the host, executable ABI, CAD ABI and selected instrumentation realm
separately. Verify the realm's actual `Process.arch` and module bases in a small
identity capture before installing archive hooks. Preserve failed setup evidence
and catch dependency initialization errors inside the capture runner. The
[usage ledger](../../../../../re/solidworks/records/Tupni2026.md) records this case.

The matching x64 Python/Frida pair rejected `realm=emulated` with an unsupported
OS error. `realm=native` then attached, reported the x64 target modules and
detached successfully. Choose a realm from observed provider support and confirm
its actual architecture. Do not derive that parameter solely from the host OS
or the fact that Windows emulates the application.
