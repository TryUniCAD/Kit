# Fusion parameter allocation watermark

## Expectation

In captures without parameter removal, the unsigned word at body offset 11 of the parameter collection equals the following member count.
Treating those equal values as two copies of the same count appears to reproduce those captures.

## Actual behavior

The installed arm64 `NsCommonData10.dylib` identifies the collection as `Ns::Parameters::ParameterTable`.
Its `initializeMemberSet` at address `0x170000` registers an independent unsigned 32-bit `highWaterMark` member at in-memory offset `0x1b8`.
An in-memory offset is not a wire offset.
The member's native identity disproves the assumption that its definition is another list length.

## Workaround

Preserve allocation state separately from the current member sequence.
`ParamScope.HighWaterMark` is an explicit writer input; only the list count is derived from `MemberIds`.
Do not infer a general deletion or reallocation policy until controlled captures and the allocation implementation establish it.
The existing dense-ordinal source-proof profile remains deliberately narrower than the archive reader.

See the [data model](../../Reference/Research/FusionDataModel.md#parameter-collection).
