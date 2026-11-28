# Hopper procedure bodies can absorb tail targets

## Expectation

A procedure assembly or callee response describes only the requested original native function.

## Actual behavior

The 2026 CString investigation used REA with Hopper on the pinned `swccu.dll`.
Its procedure API did not expose complete body ranges.
The assembly response for unsigned-word reader `0x31a342e0` included the distant DB routine at `0x31a41900`.
The callee response for wide writer `0x31a34590` also attributed its long-length call to `0x31a37be0`.

Original relative-call bytes at `0x31a346a5` instead resolve to `0x31a34880`.
The original export table binds that target to the unsigned-long writer.
PE runtime-function extents and LLVM disassembly independently agree.
Those facts do not establish a complete or exclusive Hopper function graph.

## Workaround

Use provider metadata as a navigation aid when body ownership is unavailable.
Resolve original call operands and imports before assigning primitive widths.
Hash complete original PE runtime-function spans, following chained unwind ownership when present.
Disassemble those exact ranges with an independent tool.
Retain provider limitations and report the disagreement.
Do not publish vendor listings or repair the evidence by silently trusting another symbol label.

The [CString primitive record](../../../../../re/solidworks/records/CStringArchive2026.md) records the exact modules, function hashes and call sites.
No target execution was required for this comparison.
