# ARM64X ordinals have different caller views

An AMD64 SOLIDWORKS model module imports framework functions by ordinal. The available original framework DLL is ARM64X. Its unmodified ARM64 export view maps the same ordinal numbers to unrelated bodies. Decoding those bodies as the AMD64 caller's operations produced incompatible argument and object layouts.

Read the original dynamic-view metadata and reconstruct the declared caller view in memory. Follow the resulting x64 stubs to the CHPE-classified ARM64EC bodies, then resolve their auxiliary IAT against the ordinary import table. Keep the original file hash and report the derived view separately. Do not alter the image on disk or infer code ownership from the nearest export label.

The proof applies to the pinned English resource and inspects 1,735 declared view fixups. Live resource handle selection and other locales need separate evidence. [Original module and both ordinal paths](../../../../../../re/solidworks/records/FreecadCylinderNameResource2026.md)
