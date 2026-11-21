# English parameter-name resource and the ARM64X MFC route

Task `B04-SW2026-FREECAD-CYLINDER` belongs to `/root/assembly_occurrence`. Root owns integration and native tests in PR #121. The English naming rule extends the original parameter binding. Primitive lowering and native custom-name lifecycle remain open. [Native parameter binding](FreecadCylinderNativeParameter2026.md)

## Result and bounds

Resource ID `0x2e56` is `Thickness` in original `sldresu.dll`, language `1033` (`en-US`), SHA-256 `531cf5d1c913f60f707652f0ecae600313d0970f7e649dcadec64983c484e111`. The selected RT_STRING owner is type `6`, block `742`, slot `6`. The other five inspected images contain zero matching entries. The live application resource handle remains unmeasured.

The actual native comparison is case-insensitive wide text. Under that pinned English resource, the proposed `Radius` and `Height` leaves both differ from `Thickness`. The inspected setter therefore adds no `f2c` mask for either name. A fresh ordinary private parameter's existing constructor-zero `f2c` remains zero through this branch. A parameter previously named `Thickness` can retain mask `0x1`: this setter ORs the mask on equality and does not clear it on a later nonmatch.

These conclusions qualify this finite source rule only. They do not establish custom-name syntax, collisions, equation references, live resource selection, driver edits, native save/reopen or full FreeCAD source preservation. All CAD processes, held-out reads, generated native files and shared checkout writes in this tranche are zero.

## Correct caller architecture is necessary

The provided original `mfc140u.dll` is ARM64X: 12,118,600 bytes, SHA-256 `88beebf73667ab0d603355f54562aa9cf9316f4d585a40ec93430c6715ffc8d1`. Its raw ARM64 export view maps ordinals `8161` and `2909` to unrelated bodies for the AMD64 model caller. Treating the raw view as its x64 import binding is refuted by the actual argument/object dataflow.

ARM64X exposes architecture-specific views through loader transformations. The research reader applies only the image's declared dynamic fixups to an in-memory copy, following the [Microsoft architecture description](https://learn.microsoft.com/en-us/windows/arm/arm64x-pe) and [LLVM's hybrid-view reader](https://github.com/llvm/llvm-project/blob/llvmorg-21.1.0/llvm/lib/Object/COFFObjectFile.cpp). The source contains 1,735 fixups: 1,697 values, four zero-fill operations and 34 deltas. The resulting header is AMD64-compatible. No binary is modified on disk or executed.

The original CHPE code map independently distinguishes ARM64, ARM64EC and x64 ranges. The selected exports enter x64 relative-jump stubs, which lead to the actual ARM64EC implementations. The auxiliary IAT is then mapped through the original CHPE and ordinary IAT bases, rather than guessed from a neighbouring import address. [LLVM's published structures](https://github.com/llvm/llvm-project/blob/llvmorg-21.1.0/llvm/include/llvm/Object/COFF.h) define those metadata fields.

Seven recorded method windows retain their original code bytes. The comparison import thunk's address operands change through the declared view fixups. Both original and derived hashes are recorded. Treating that thunk as unchanged would lose its actual auxiliary-IAT ownership.

| Model import                     | Correct hybrid export | x64 stub target | Actual operation                                                   |
| -------------------------------- | --------------------- | --------------- | ------------------------------------------------------------------ |
| `0x4cd34e70`, MFC ordinal `8161` | `0x1806ae170`         | `0x18034a4f0`   | Find a resource handle for the string ID and load its owned string |
| `0x4cd34e80`, MFC ordinal `2909` | `0x180699f80`         | `0x18037f2a0`   | Tail-call the wide case-insensitive CRT comparison                 |

The comparison implementation reaches ARM64EC thunk `0x180338538`. Its auxiliary IAT slot `0x1809947b0` points to exit thunk `0x18066c3c0`, which independently loads ordinary slot `0x1806c87b0`. That import is `_wcsicmp` from `api-ms-win-crt-string-l1-1-0.dll`. The exit thunk also validates the metadata-based slot correspondence rather than assuming that two arrays have the same index. This closes the comparison's case rule without using the unrelated raw ARM64 ordinal implementation.

## Loader and locale ownership

The correct resource-load body at `0x18034a4f0` calls handle search `0x180660450`, then the explicit-handle loader `0x18034a400`. Both use block lookup `0x18034a340`. That lookup computes the block from `(id >> 4) + 1`, uses RT_STRING type `6`, then traverses the length-prefixed UTF-16 entries to `id & 15`. Its imported calls resolve to `FindResourceW`, `LoadResource`, `LockResource` and `SizeofResource` through the correct auxiliary-IAT mapping.

The handle search tries a candidate at current state `+0x18`, an extension list at `+0x88`, an additional candidate at `+0x98`, and the alternate list-order path selected by the state flag. The record does not assign a stronger class or locale meaning to those state fields. The selected `FindResourceW` call passes no explicit LANGID. The native code therefore does not justify replacing the actual selected resource with the host's language preference or a universal English constant.

The scoped rule requires the pinned English resource owner. Other localized resource binaries and arbitrary changed MFC module chains remain outside it. The source resource directory proves the `1033` entry, while a live selected HINSTANCE has not been measured. An eventual native custom-name trial must preserve that distinction in its environment and receipt.

## Reproduction and primitive continuation

[`PinCylinderNameResource.py`](../../tooling/sw2026/freecad_cylinder/PinCylinderNameResource.py) takes the original image directory and an unused JSON output path. Its adjacent [`NativeNamePe.py`](../../tooling/sw2026/freecad_cylinder/NativeNamePe.py) parses only file-backed PE metadata, selected resources, declared ARM64X transformations and the traced branch/import instructions. Both use Python's standard library. The output includes six image identities, original versus hybrid export targets, code-map ranges, eight hash-bound method windows and the two explicit-name rule results. It never writes the transformed binary or a vendor listing.

With the identified English resource, `Radius` and `Height` bypass the `Thickness` flag update. The existing length and name constructors can carry those leaf names. Native edit and reopen still need measurement on a complete source-preserving lowering. [Machine-readable source pins](FreecadCylinderNameResource2026.json) · [Source admission](FreecadCylinderAdmission2026.md)

The next native dependency is independently locked source cases followed by measured names and both real drivers through open, edit, rebuild, save and fresh reopen. The other eleven primitive parameter owners, source metadata, material reference and absent source support/sketch still require their own admitted mapping.

See the [ARM64X gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Interop/HybridPeOrdinalsHaveDifferentViews.md) and [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md).
