# Downstream application construction

The [source record](../../../../../re/solidworks/records/DownstreamApplicationConstruction2026.md) binds the actual SOLIDWORKS 2026 executable `CAmApp` constructor and its explicit zero assignment to downstream-enable runtime member `+0x464`. It includes full original function and RTTI hashes, the actual static-object caller and the unchanged prior save/store evidence.

Use this finding to distinguish initial assignment from later conditional save activation. It does not establish the final startup value, a live preference, selected UI manager installation, a saved standalone cache or a wire default. No SDK or writer behavior changes.

Verification was static original-image and metadata inspection only. No application, VM, preference/license, saved or hidden CAD input, codec, schema or tests ran. Native and held-out acceptance remain unmeasured. The existing [constructor-prefix gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/ConstructorPrefixIsNotFinalState.md) remains relevant to lifecycle claims.
