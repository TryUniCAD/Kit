# Hybrid PE exports depend on process architecture

## Expectation

The on-disk export table of a System32 DLL identifies the implementation reached
by an x64 application's ordinal import.

## Observed behavior

The pinned `swccu.dll` imports MFC count functions using ordinals `12087` and `14278`.
The retained System32 `mfc140u.dll` has raw PE machine `0xaa64`, and LLVM identifies
it as ARM64X. Its raw export entries at those ordinals do not identify the expected
count pair. The [native owner record](../../../../../re/solidworks/records/CommonPartOwners2026.md)
records the exact file identity and import addresses.

Microsoft's [ARM64X description](https://learn.microsoft.com/en-us/windows/arm/arm64x-pe)
explains that the OS transforms the visible architecture and entry points according
to the loading process. The disk header defaults to an ARM64 presentation. A raw
ordinal lookup therefore does not bind the implementation used by x64 emulation.

## Workaround

Keep raw file identity, actual process architecture, mapped headers and effective
export resolution as distinct observations. The [runtime-view probe](../../../../Changes/Solidworks/Model/SolidworksMfcRuntimeViewInspection.md)
performs bounded inspection in its own process and never invokes the count methods.
Its execution remains pending when this gotcha is introduced.

Even matching mapped exports do not prove the instruction set or a count rule.
Trace the resolved code and its complete native boundaries before admitting a schema.
Do not substitute an x86 table, infer an extra count escape, or clear a provisional
marker from a matching corpus count alone. Keep runtime captures outside checkouts.
