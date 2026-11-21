# Typed ordinary SOLIDWORKS mate-list codec

The SDK now has a separate typed codec for ordinary version-19000
`Config-0-MatesList` streams. It reads and re-encodes empty, coincident,
parallel and positive-distance lists using the actual SDK resolved map.
Inherited occurrence references retain object identity. The resolved mate
group's serialized children remain unchanged.

`ReadMatesMut`, `WriteMatesMut` and `MatesGraph` live under
`src/convert/adapters/solidworks/Archive/Mates/`. Both directions require a
typed resolved assembly graph. The stored signed counter must match that
graph. Unknown mate families, nonplane wrapper references, unsupported
schemas and versions, malformed input and trailing bytes fail explicitly.

The public adapter route is unchanged. This codec does not establish a new
native writer, held-out qualification, or complete semantic mate admission.
Distance-display packed values retain the existing typed binary64 codec and
remain visible in coverage diagnostics.

The disclosed process verifier accepts an authorized six-assembly manifest
and its independent linked-stream receipt:

```sh
uv run --isolated --frozen --extra dev --python 3.11 python -I -B re/tooling/sw2026/SdkMatesProcess.py \
  --cohort /absolute/path/to/InputManifest.json \
  --linked-proof /absolute/path/to/LinkedMatesExact06.json \
  --output /absolute/path/to/UnusedMatesProof.json
```

Six fresh processes pass exact stream bytes, typed graph readback,
inherited identities and six-byte empty framing. They reject 84 malformed
cases. A separate guarded generated distance-mate bundle passes the same
process checks, including 14 negatives. Black and steering pass. These are
local integration and policy results; remote CI and native qualification
are separate evidence.
[Receipt](../../../../re/solidworks/measurements/2026/SdkMatesListCodec01.json)
[Format and ownership record](../../../../re/solidworks/records/SdkMatesListCodec2026.md)
[Endpoint kind guard](../../../Gotchas/Conversion/Solidworks/Archive/Assembly/MateWrapperKindNeedsAnExplicitGuard.md)
