# Guard public writes from strict cold SOLIDWORKS JSON

## Behavior

The [qualified publication harness](../../../../re/solidworks/EncoderBoundary/CheckQualifiedPublication.py) now guards each registry and direct writer call.
Its input is the complete strict SDK readback of a generated part, serialized through Kit JSON.
This exercises the public writer's complete cold-readback comparison.

The audit hook refuses file access, process launches, sockets, native-library loading and registry access during each public call.
Source construction, JSON parsing and offline receipt loading occur before the guarded public calls.
The existing exact archive and executable-identity checks remain unchanged.
Rejected requests must preserve caller stream bytes and cursor position.

The guard covers a different boundary from the existing authored-input publication and prepared-constructor replay checks.
The [integration test](../../../../tests/Research/EncoderSolidworks/QualifiedPublicationTests.py) uses the existing complete-suite execution path.
No workflow, runner or production API is added.

## Verification

Run the harness with the pinned environment and a trusted checkout.

```powershell
python re/solidworks/EncoderBoundary/CheckQualifiedPublication.py --root .
```

The [recorded result](../../../../re/solidworks/measurements/2026/EncoderRoundTrip/GuardedPublicReplay.json) binds the harness and relevant production source digests.
It records 32 guarded public calls with zlib-ng `1.3.1`.
The four previously measured cases each passed through the registry and direct writer.
All eight successful writes matched their exact measured archive bytes.
Eight changed executable identities and sixteen oversized numeric observations refused publication without changing caller streams.
Runtime external-access attempts and native launches were both zero.
After integration with the focused signed validator, the process check passed in 8.65 seconds at revision `b0023ba4e4`.
The checked public writer behavior and all eight measured archive digests remained unchanged.

## Limits

This result adds offline public-boundary evidence.
It does not add native observations or qualify additional source families.
The [existing SP04.1 measurement qualification](../../Solidworks/Construction/SolidworksEncoderOracleBuild.md) supplies the native evidence.
The caller remains responsible for the provenance of the unsigned offline receipt.
The exact archive digest, locator, epoch and qualified executable identity remain mandatory.
