# Assembly solve status follows active native results

`moAssembly_c.f1570` is derived solve status. Allocation initializes it to
zero, but native state transitions can replace zero before saving. The 2026
resolved section stores a `u16`; the setter and getter use the full 32-bit
runtime member at `+0x1570`.

## Binary and provider identity

The original `sldmodu.dll` is build `34.5.2.0604`, base `0x4b140000`,
SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
The [saved native Hopper database](../measurements/2026/MarkupHopperAnalysis01.json)
identified four procedure entries that call the setter. Original call operands
confirm all four. The private provider response `AssemblyStatusCallers01.json`
has SHA-256 `3ae8d4d946dba11efb98c9b7a284db0cc282233f0bc2275413a4ef99e805e54d`.
No native listing or database is included. These observed call sites do not
prove that there are no other callers.

| Procedure | Original half-open range | Code SHA-256 |
| --- | --- | --- |
| Assembly status getter | `[0x4b69e140,0x4b69e147)` | `f8807ef0a4ab0bd904aa1977db06ff89697f7f6f238a327fa5351b22a7d2f38e` |
| Assembly status setter | `[0x4b6b7950,0x4b6b7957)` | `6da594f8e0c1144ad644cb56c02a5a36bc42d786184154b405343966943fc7ec` |
| Mate update branch | `[0x4bc8fde0,0x4bc9013f)` | `945298f42a70870d421c4ab16e7a472b0c49ee9e5d11f69770d18047a10cd341` |
| Two-component update branch | `[0x4bc90140,0x4bc9052b)` | `6f1b9b7bfc7cb06233d2705c76c29581c16ed0ffea3f319171cde2783aaa1ecc` |
| Reference state update branch | `[0x4bbc8f20,0x4bbc937e)` | `39debb02bcb520c6666038ea47bcee419d59bdf75f5345986a24ea42ea003e48` |
| Solve state walker constructor | `[0x4b6f80a0,0x4b6f80f3)` | `6037af9700b38913ea019f21427106d34b9bf76c1c0e579146690f1b9ebfc812` |

## What the setters receive

- `0x4bc9008a` writes the result of a scan that filters on the active
  configuration. Predicates at `0x4bc8ffde` and `0x4bc8fff7` gate each item.
  For admitted items, virtual `+0x1f90` supplies a state. The branch selects
  `5` if any admitted item supplied `5`; otherwise `2` if any supplied `2`;
  otherwise `3` or `1` from a separate local flag. The caller treats changes
  to `5` and `2` specially when writing assembly runtime field `+0x1830`.
- `0x4bc904bb` receives walker result `+0x108` after a reference or viewer
  component update. `0x4bbc9264` recomputes the same result after removing a
  reference, and writes only if it changes. The shared walker constructor
  initializes `+0x108` to `1` and starts a native assembly walk. That
  initialization is still a seed.
- `0x4b6cf1e7` sets a flexible referenced assembly's result. It selects `5`,
  `2`, `3` or `1` from prior reference-state flags. The call's range is the
  reverse-linked fragment `[0x4b6cf16e,0x4b6cf257)`, SHA-256
  `ef38e939485cac620a8b26bc93182189ae37f5c82c3bc79dc166ffe709a88637`.

These are static facts for the observed branches. They refute a universal zero
or component-count rule. The full enum names, forced solve paths, unresolved
contexts and the final value for a fresh ordinary no-mate assembly remain open.
Use controlled native sources and archive correlations before writer use.
