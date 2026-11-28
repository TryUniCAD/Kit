# Empty arrays do not prove element grammar

## Expectation

An array header and a computed `count × element_width` payload length are enough
to admit the payload as a fully typed graph field.

## Actual behavior

The current disclosed resolved closure has two variable array definitions.
`FUN_4bb09f20` contributes no observed payload. `dm.FUN_4bd03960` has 25 observed
eight-byte display payloads per direction. Zero bytes establish neither a
nonempty layout nor element meaning; eight bytes alone do not prove binary64.

The common native display constructor and owned update independently bind `f5b0`
to binary64 parameter values. The SDK therefore has explicit scalar decoding,
encoding and usage for that owner. The generic profile-array payload remains
unsupported when nonempty. The selected compressed-body mode does not read the
separate Parasolid byte payload.

## Workaround

Prove the element type from its actual native owner before admitting a nonempty
array. Preserve count/width headers and source-compatible field shapes, but
reject unknown payload grammar rather than passing it through as typed data.
Record element type, count, owner, length rule and observed byte count. Keep
construction/default and final native saved-state evidence separate.

See the [resolved ledger](../../../../../../re/solidworks/records/ResolvedBodyGrammar2026.md),
[common engine rules](../../../../../../re/solidworks/records/RadialEngineFieldRules2026.json)
and [change entry](../../../../../Changes/Solidworks/Archive/SolidworksTypedResolvedGraph.md).
