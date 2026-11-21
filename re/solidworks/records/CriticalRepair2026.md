# SOLIDWORKS 2026 critical repair rejection

Status: rejected. The generated triangle returns no document, error `4194304`
(`0x400000`), zero warnings, between two healthy original controls.
The [staged measurement](../measurements/2026/FreshPartStages.json) retains the
specific `open_start` and `open_return` stages and exact executable identity.
Neither explicit rebuild nor later queries ran for the candidate.
Both controls rebuilt one solid, volume `8.000000000000001e-6 m³`, area
`0.0028 m²`, center `(0,0,0.005) m`, with zero open or feature errors/warnings.

The [2026 API enumeration](https://help.solidworks.com/2026/English/api/swconst/SOLIDWORKS.Interop.swconst~SOLIDWORKS.Interop.swconst.swFileLoadError_e.html)
names this bit `swFileCriticalDataRepairError`. This is a reported critical
data-corruption condition, not the missing-display-data bit.

## API mapping

The following observations bind to `sldappu.dll`, SHA-256
`50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf`,
16,519,768 bytes, preferred image base `0x453f0000`.

| Site         | Native observation                                                             | Confidence and limit                                                       |
| ------------ | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| `0x458a288a` | `auAm_c::apiOpenDoc` compares the 32-bit application member `+0x31c` with zero | Confirmed static instruction; runtime input result not yet traced          |
| `0x458a2897` | Nonzero selects an OR of `0x400000` into returned API error flags              | Confirmed SDK mapping, not a format validator                              |
| `0x457e3d86` | Writes one to `CAboutDlg+0x31c`, a different runtime object                    | Refuted application-flag interpretation; excluded from the repair observer |
| `0x45d718ca` | An exception-handler-style path writes 32-bit one to application `RAX+0x31c`   | Confirmed selected setter; the handler's initiating exception is unknown   |
| `0x45a29b50` | The latter path queries `uiEnvironment_c::getBOOL`, key `0x461`, default zero  | Environment preference, not a recovered model validator                    |

Instruction decoding was repeated from the exact established boundaries.
Arbitrary nearby byte offsets initially produced misaligned decoding and supply
no field evidence. The target module digest was independently recomputed.
No vendor listing is included here.

## Next observation

The full and repair native profiles record the confirmed setter site and the API comparison.
It retains the application pointer, thread, instruction location and raw adjacent
32-bit words at `+0x314/+0x318/+0x31c/+0x320`.
Only `+0x31c` has the critical-error mapping above.
The other words remain unclassified runtime observations.
The initially selected `0x457e3d86` site was excluded after RTTI established a
different owner: `CAboutDlg` vtable `0x45ee5f38`, slot 96, points to
`0x457e3310`. Its `+0x31c` word is not the application's repair flag.
Matching offsets and immediate values do not establish matching field ownership.
The runner verifies the additional application module hash before hook activation.

Neither a serialized-field change nor a writer default follows from these runtime
application flags alone.

The `repair` profile arms only these two instruction sites. Clean inspection
returns the critical repair error, while earlier full profiles terminate the same
candidate process with exit code 1. These observations do not prove the reason
for the difference. The smaller profile reduces the instrumentation boundary;
its behavior must be measured on both the control and the candidate.

## Initial document update

The 2026 application exception metadata localizes the selected catch-all handler
to state 9, protected range `[0x45bdc975,0x45bdc98d)`, in the implementation at
`0x45bdc480`. Its only call, at `0x45bdc986`, dispatches template slot `+0xf8`.
The selected runtime template is `uiPartDocTemplate_c`, executable vtable RVA
`0x1b848`. Its target RVA `0x1680c` is an import thunk for application method
`uiModelDocTemplate_c::InitialUpdateFrame` at `0x45bda7b0`.

The [controlled frame capture](../v2026/evidence/TupniInitialFrame.json) uses
silent writable opening without a save request in every run. Both locked input
hashes remain unchanged. The two-hook repair control opens and rebuilds cleanly;
its candidate reaches the confirmed setter and exits with code 1. Matching the
open mode therefore does not by itself remove the earlier outcome difference.

The one-hook frame control also opens and rebuilds cleanly. It records 79
handled system exceptions. Its candidate instead records an access violation at
`SLDMFCU+0x45df0`, preferred address `0x3c765df0`, reading address `0xc` with
`RCX=0`. The captured native exit status is signed `-1073741819`, unsigned
`0xc0000005`. No document returns to the public open call.

Static instruction checks corroborate the first part of the provider backtrace:
the copy constructor `moVisualProperties_c(const moVisualProperties_c*)` at
`0x3c9209e0` passes its null source to the leaf that reads `source+0xc` at
`0x3c920a5d`. The caller at `0x4c1f4737` supplies the source previously returned
by model virtual slot `+0x1040` at `0x4c1f46d0`. The copy path follows missing
visual state on the current base configuration, which is model member `+0xd78`,
not a peer model.

The display-state service's fallback at `0x327aad45` reads concept member
`+0x78`; the active concept serializer owns that same `f78` field. The research
model builder previously left this pointer null. The
[visual construction record](VisualConstruction2026.md) now derives its owned
visual object and mandatory material member from native default constructors.
The [next clean measurement](../measurements/2026/FreshPartModelAppearance.json)
now opens the generated replacement without errors or warnings between healthy
controls. Its sketch and extrusion are suppressed and body count is zero.
The null-source opening defect is repaired; geometric acceptance is unfinished.

The system-exception backtraces also contain non-code values in the healthy
control. No unvalidated frame is treated as a call-chain fact. No exception is
suppressed or application preference changed. These are diagnostic captures,
not generated-output acceptance.
