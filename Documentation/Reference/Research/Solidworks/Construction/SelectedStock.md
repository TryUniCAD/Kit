# Construct an explicitly selected stock body

## Purpose

Use the internal SDK constructor for one actual stock body and its ordinary through-all circular cut. The public writer registry is unchanged.

## Before you start

Prepare an admitted `ThroughPartSpec` and the corresponding `PartBuildInput`. Use archive version 19000.

The stock must be the first rectangular mid-plane boss. The free circular cut must remain inside that stock on the same principal datum.

Retain the actual `ThroughStock` object. An equivalent reconstructed object does not supply the same ownership.

## Procedure

1. Create `SelectedStock((InputValue.StockValue,), "selected", 19000)`.
2. Call `MakeScopedThru(InputValue, SettingsValue, ScopeValue)`.
3. Read the complete candidate from `ResultValue.PartValue`.
4. Read its actual selected-body graph from `ResultValue.ScopeValue`.

Import each symbol from its defining module:

| Symbol           | Defining module below `convert.adapters.solidworks.Archive.Construction` |
| ---------------- | ------------------------------------------------------------------------ |
| `SelectedStock`  | `BodyScope.SelectedStock`                                                |
| `MakeScopedThru` | `ThroughAll.MakeScopedThru`                                              |
| `ScopedPart`     | `BodyScope.ScopedPart`                                                   |
| `StockBodyGraph` | `BodyScope.StockBodyGraph`                                               |

## Expected result

The result retains the actual stock model, part root, boss, atom, wrapper and cut. The candidate contains all ordinary streams and the complete native container.

No kernel body or automatic-selection runtime field is transmitted. The existing scope-zero `MakeThroughPart` output remains unchanged.

Three generated outputs match the earlier research constructor exactly. The Front bytes match the input measured in the successful four-process native lifecycle.

## If the task fails

Missing, multiple or foreign owners raise an error. Restore the actual stock reference before retrying.

Existing output atoms, selected scope, retained ghost bodies or altered history also raise errors. Use a fresh supported input.

The mode `automatic` is unsupported. Do not convert that request into explicit selection without a separately proved semantic projection.

## Reproduce the process boundary

Run `CheckSdkStockScope.py` with an explicit preparation root, original disclosed reference root and unused output directory. The runner checks the source manifest before and after execution.

The 31-worker selected process checks exact outputs, linked aliases, strict rejection and the matched scope-only stream difference. The existing 31-worker through-all process checks compatibility separately.

Use the checked-in `CheckThroughAllCold.py --preparation-root PREPARATION --output UNUSED_DIRECTORY` interface for compatibility replay. The private legacy coordinator retains its original positional interface.

This constructor has no public registry admission or original held-out acceptance. [Construction evidence](../../../../../re/solidworks/records/SdkSelectedStockConstruction2026.md) [Change entry](../../../../Changes/Solidworks/Generation/Extrusion/ThroughAll/SolidworksSelectedStockSdk.md)
