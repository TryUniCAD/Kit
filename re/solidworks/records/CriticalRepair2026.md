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

| Site | Native observation | Confidence and limit |
| --- | --- | --- |
| `0x458a288a` | `auAm_c::apiOpenDoc` compares the 32-bit application member `+0x31c` with zero | Confirmed static instruction; runtime input result not yet traced |
| `0x458a2897` | Nonzero selects an OR of `0x400000` into returned API error flags | Confirmed SDK mapping, not a format validator |
| `0x457e3d86` | A repair/reporting path writes 32-bit one to application `RSI+0x31c` | Confirmed selected setter; caller function boundary remains separate from its nearest export label |
| `0x45d718ca` | An exception-handler-style path writes 32-bit one to application `RAX+0x31c` | Confirmed selected setter; the handler's initiating exception is unknown |
| `0x45a29b50` | The latter path queries `uiEnvironment_c::getBOOL`, key `0x461`, default zero | Environment preference, not a recovered model validator |

Instruction decoding was repeated from the exact established boundaries.
Arbitrary nearby byte offsets initially produced misaligned decoding and supply
no field evidence. The target module digest was independently recomputed.
No vendor listing is included here.

## Next observation

The full native profile records both selected setter sites and the API comparison.
It retains the application pointer, thread, instruction location and raw adjacent
32-bit words at `+0x314/+0x318/+0x31c/+0x320`.
Only `+0x31c` has the critical-error mapping above.
The other words remain unclassified runtime observations.
The runner verifies the additional application module hash before hook activation.

The underlying file-format validator is not identified yet.
Neither a serialized-field change nor a writer default follows from these runtime
application flags. New controlled captures are pending.
