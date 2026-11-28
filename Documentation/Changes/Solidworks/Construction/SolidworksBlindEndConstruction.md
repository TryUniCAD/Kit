# Native blind end and parameter construction

The SDK has a typed construction primitive for an ordinary forward blind boss's parameters and end specification.
It derives parameter names and values from the native dimension roles and the authored depth.
It creates fresh parameter, name and end-spec nodes through the shared archive object model.

`BlindEndInput` takes metres, an explicit forward direction and archive version 19000.
`MakeBlindParam` constructs the selected `D1`, `D2`, `D3`, `D4` or `D19` parameter.
`MakeBlindEnd` retains the caller's actual distance, draft and from-end display graphs.
It validates concrete classes, live values, local handles and distinct dimension identities before creating its complete owner.

The caller supplies the dimension, display, style, feature and history graphs.
The caller also allocates the actual dimension IDs through its header allocator.
The transient `D19` graph remains required even when its branch emits no display bytes.
See the [identity rule](../../../Gotchas/Conversion/Solidworks/Model/Dimensions/DimensionAndParameterIds.md)
and [transient-dimension rule](../../../Gotchas/Conversion/Solidworks/TransientDimensionsConsumeIds.md).

The primitive reads no file, source saved bytes or research data.
It imports no CAD runtime and does not enable the public SOLIDWORKS writer.
Unsupported versions, reverse direction and invalid depth or graph references fail explicitly.
The [construction ledger](../../../../re/solidworks/records/SdkBlindEndConstruction2026.md) records every field rule and remaining ownership boundary.

The frozen generated process check passes ten exact SDK stream comparisons across two independent polygon topologies and depths.
It rejects eighteen malformed cases and records zero runtime input-file reads.
The resolved stream grows with the authored topology.
The [verification receipt](../../../../re/solidworks/measurements/2026/SdkBlindEndConstruction01.json) binds the exact source and generated artifacts.
Native and held-out qualification remain separate requirements.

Existing research builders have extra object accessors.
The proof installs SDK nodes after those builder operations.
See the [typed-field boundary](../../../Gotchas/Conversion/Solidworks/Archive/Construction/PlainArchiveNodesUseTypedFields.md) before delegating an older builder directly.
