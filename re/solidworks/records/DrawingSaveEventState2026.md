# Blank drawing save event and target state

The generated blank returned `[false,1,0]` from `SaveAs3` and left a zero-byte target. A deliberate event 7 veto on the reduced native blank returned the same status and left the target absent. Both lanes emitted `[7]`. The difference appears in the first target metadata snapshot after the synchronous call returns. [Native receipt](../measurements/2026/DrawingBlankSaveEventStateNative01.json)

## Repeat the comparison

Use a private copy of the frozen event-state deck. Its `Inputs/` contains the three disclosed blank drawings from the original save-event trial. Its `Tools/` contains the original eight support tools, the corrected event observer and the state observer. The manifest binds the input and tool hashes, the earlier native receipt and the calibration rule. [Original observer and trial](DrawingSaveEvents2026.md) · [State observer](../../tooling/sw2026/InspectBlankDrawingSaveEventState.py)

```text
python -B Tools/InspectBlankDrawingSaveEventState.py Trial.json --packet-sha256 63d68733f3e7f28732f7b927c7d0044da38829ce5ba5eeb124cf7d4b1c189455
```

Add `--verify-only` to check custody without starting SOLIDWORKS. The native run creates `DrawingSaveEventStateResults/` and writes `Progress.json` and `DrawingBlankSaveEventStateResults.json`. Use an unused deck. The exit status reflects the quality of the observation batch. Each lane records its own `SaveAs3` status.

The observer opens and rebuilds each disposable copy through the original COM sequence. It records `GetPathName` and `GetSaveFlag` before save, then reads target existence and extent before the call, during `FileSaveAsNotify` and immediately after the call returns. The typed sink advertises ordinary storage ordinals 9 and 28 and autosave ordinals 11 and 48. Each passive lane returns zero from the event sink. The separate veto lane uses the same reduced native bytes and returns one during event 7. The three native controls save and reopen with fresh processes.

## Native result

All five lanes opened and rebuilt with zero errors or warnings, ten tree rows, the expected working path and a true save flag. The input and output paths matched across lanes. The target was absent before the call and at the event 7 snapshot in every lane. The eight oracle processes matched SOLIDWORKS `34.5.2.0604`, and the input hashes remained immutable.

| Lane | Synchronous events | SaveAs status | Target after return |
| --- | --- | --- | --- |
| Pristine before | `[7,9,28]` | `[true,0,0]` | 18,434 bytes |
| Reduced native | `[7,9,28]` | `[true,0,0]` | 17,915 bytes |
| Generated | `[7]` | `[false,1,0]` | 0 bytes |
| Reduced native with deliberate veto | `[7]` | `[false,1,0]` | Absent |
| Pristine after | `[7,9,28]` | `[true,0,0]` | 18,926 bytes |

The generated runtime listener aggregate, document dispatch result and target storage state remain unmeasured. The static branch map identifies the addresses that would distinguish them. [Post-event branch map](DrawingSavePostEventBranches2026.md) · [Save status gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/DrawingVetoAndSaveFailureShareStatus.md)
