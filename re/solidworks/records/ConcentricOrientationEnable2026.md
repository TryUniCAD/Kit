# Concentric cylinder orientation enable ownership, SOLIDWORKS 2026

The pinned 2026 selected-face creation path explicitly enables the cylinder wrapper's private orientation state. The serializer also reconstructs the state on load when the wire record carries a local vector. The cold-open caller that refreshes cylinder geometry before solve remains unresolved.

Task `B04-SW2026-MATES-CONCENTRIC` is owned by `/root/flag_ownership` and delivered in PR #121. This checkpoint binds the enable caller and concrete receiver in the installed build.

## Exact identities and method

Both original x64 PE images are release `34.5.2.0604`:

| Module | Preferred base | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `sldmodu.dll` | `0x4b140000` | 46,536,280 | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `slduiu.dll` | `0x48ea0000` | 36,036,696 | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` |

The [numeric evidence](ConcentricOrientationEnable2026.json) records original-byte SHA-256 values for 14 complete native functions or leaves, all 12 applicable chained unwind fragments, 12 call instructions, 14 instruction windows, two concrete primary RTTI tables and seven virtual cells. Named callers are bound to exact export entries, not the nearest disassembler label. The private replay reads only the pinned original DLLs and emits metadata. Original binaries and listings remain outside the checkout.

No CAD, COM, guest, product, schema, codec or test execution occurred. No saved native CAD payload or sealed input was opened. REA had no open target and retained cleanup was pending; no target or cleanup operation was acquired by this worker. The instruction review used LLVM on the unmodified original PE images.

## Confirmed static creation rule

1. Exported `uoSelectedObj_c::createMateEntity` occupies `[0x4a10a0d0,0x4a10a4bd)`, SHA-256 `233180f6a231af0624eaf74faadb5c947f6186a7a5dcbe063e866a8788b91653`. Its ordinary branch excludes the separate mate-type 16/18 branch and earlier coordinate, plane, line and point cases. At `0x4a10a1c6` it tests the cylindrical classification. A true result dispatches the selected object's `+0xd58` at `0x4a10a1d7`.
2. The actual `uoSelFace_c` constructor `[0x4a0c05b0,0x4a0c065b)` publishes primary vtable `0x4a81e258`. Its complete-object locator resolves the exact `uoSelFace_c` RTTI type. That table's `+0xd58` points to `[0x4a0c9f90,0x4a0ca020)`, SHA-256 `886cb5260ce8ea88eb00ce786c64054817bd900b361341ab642f563fd1c6ac7e`.
3. This concrete factory rejects the selected-object special guard or a nonnull `+0x3e8`. It resolves an actual face through imported `moCompFace_c::getFace(1,0,null,null)`, requires imported `gcFace_w::isCylindrical`, obtains the actual component reference, and requests `moCylinderRef_w::GetThisClass`. It then calls `uoSelectedObj_c::iMakeRefWrapper` at `0x4a0ca00d`.
4. `iMakeRefWrapper`, `[0x4a1174f0,0x4a11781f)`, obtains the actual edit-target chain and invokes the imported `moRefWrapper_c::createRefWrapper` at `0x4a117568`. The exact imported symbol resolves to model export `0x4c30f400`. The successful generic factory invokes its returned wrapper's `+0x3b8` at `0x4c30f69d`. This is a fresh creation update; it is not evidence of cold-open scheduling.
5. The nonnull common return tail of `createMateEntity` sets Boolean argument `DL=1` at `0x4a10a493`, sets the actual returned wrapper as receiver, and invokes wrapper `+0x328` at `0x4a10a498`. The cylinder's concrete primary table `0x4cd938c0`, independently bound by RTTI, maps this slot to `[0x4c331bf0,0x4c331cb3)`, SHA-256 `aa050e3ac6b80c234ed6bb1b11e12eb52c8ad1cb07cbb2515ed9192586b3b197`.

This establishes the conditional selected-face mechanism. It does not establish that every public API creation route uses this selected-object entry, or that every failed selection yields a cylinder wrapper.

## State and wire ownership

The cylinder Boolean operation uses private pointer `this+0x108`. With true and an already present state it returns without replacing the state. With true and no state it allocates `0x68` bytes and constructs the state from the wrapper's actual current world unit axis `+0xe8`, point `+0xd0`, and wrapper receiver. With false it clears and destroys the state. Its constructor is `[0x4c306c60,0x4c306ded)`, SHA-256 `f47a24a84b3f0531a7a452e07a907b1027ae5da3a0a56920c4357d29ba51eac2`.

The inverse-placement local-axis rule and private field ownership remain as documented in [the construction record](ConcentricSupportSnapshotConstruction2026.md). For an actual different-model wrapper with an actual transform, private state `+0x18` is derived using that inverse placement. It is not the wrapper's world axis merely because both are vectors. No general orientation-preservation claim is added.

The actual cylinder serializer `[0x4c26f8f0,0x4c26fb27)`, SHA-256 `5e17aecfbac53fb7b0b1c55192c3fac47196f956312386c1a3a73889db3bf96b`, distinguishes the operations:

| Operation | Proven effect |
| --- | --- |
| Current store with null state | Write `u16(0)`; no optional vector |
| Current store with present state | Write `u16(1)` followed by private state `+0x18` as an `mgVector` |
| Ordinary load, version at least 4171, zero presence | Do not call enable or allocate state in this branch; on a fresh constructor-null object it stays null |
| Ordinary load, nonzero presence | Construct private state from the loaded world axis/point; transfer ownership into wrapper `+0x108`; overwrite state `+0x18` with the wire vector |
| Read compatibility extension | A signed 16-bit comparison of presence against 2 controls an additional point into state `+0x48`; this is not emitted by the current store branch |

The load transfer is `[0x4c263e20,0x4c263e96)`, SHA-256 `a3cb7905e453f176eef2d0fa90794430477308eb3beef418a8a53684b60b9aff`. It nulls the temporary source, replaces the destination pointer and releases the prior destination state. Loading a present record does not prove that the selected-face enable caller ran during load.

## Refuted generic-cache shortcut and retained boundary

`moAssembly_c::initRefWrapperCache`, `[0x4b6a7c10,0x4b6a7ced)`, SHA-256 `295e24e60ce18df826c82ba9ec6d4a47f73a451eb98e4fcd9d9b9bbaac60e8b9`, iterates collected wrappers. Before it can invoke wrapper update `+0x3b8`, it requires wrapper predicate `+0x140` to return true and the wrapper not to be lightweight. The actual cylinder table's `+0x140` points to the complete false-return leaf `[0x4b27cbe0,0x4b27cbe3)`. Therefore this helper skips an actual cylinder even if the collection contains it.

The separate next question is which current-version owner invokes cylinder geometry resolution before mate solve on cold open. The earlier `getCylinder` consumer can retain or replace private local orientation state. Constructor state, UI enable, deserialization and generic cache initialization do not prove preservation across that remaining caller boundary. No whole-word default, missing-cache neutrality, callback no-op or native acceptance is inferred here.

## Acceptance

The static proof reproduces all 14 function fingerprints, 12 call instructions and seven virtual table cells on an independent replay. Native acceptance still requires a controlled cold open, rebuild, save and reopen of a generated assembly.
