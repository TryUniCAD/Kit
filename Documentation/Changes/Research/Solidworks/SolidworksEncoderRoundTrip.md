# Reconstruct a bounded SOLIDWORKS boss for encoder research

Public native qualification remains incomplete for the new encoder cases.
The work retains the existing exact offline publication gate.

## Behavior

The [research adapter](../../../../re/automation/EncoderRoundTrip/Solidworks.py) reconstructs the existing bounded ordinary part family.
The family contains one unconstrained closed Front-plane loop of three to sixty-four straight segments and one blind boss.
The adapter uses the existing generative serializer.
It does not copy a saved stream or patch a saved payload.

`generate_candidate(document, edit=None, *, native_locator, written_at)` returns candidate bytes for a separate native measurement.
The optional edit is `{"dimension": "depth", "value_mm": 12.5}`.
The value specifies the absolute positive finite depth in millimetres.
The adapter updates the driving parameter and the feature definition together.
An edit that leaves the native driving value unchanged refuses reconstruction.

`reconstruct(document, native_locator, *, depth_mm=None)` returns the corresponding authored neutral request.
This request can enter the existing research preparer or public SDK.
Public output still requires matching native evidence for the complete regenerated archive.

## Source qualification

An authored neutral request must pass the existing bounded writer plan.
A native SDK readback must first reproduce its complete original archive through the generative serializer.
This exact-byte comparison also requires a compatible compression runtime.
The full cold-read comparison includes scaffold, geometry, diagnostics, provenance and custody metadata.
The source bytes act only as a comparison target.
They do not supply writer output.

Only a verified original projection can become the bounded authored request for a deliberate depth edit.
Extra native information, changed topology, mismatched source digests and unqualified research reads refuse reconstruction.
Sketch dimensions, relations, additional features and broader source families remain outside this milestone.
The source does not become supported through metadata removal.

Both separately authored native controls refused reconstruction at the complete cold-source check.
Their [admission record](../../../../re/solidworks/measurements/2026/EncoderVendorSourceAdmission.json) retains the exact source observations.
Each decoded control had twenty-six feature rows, one solid, a driving D1 and two retained native payloads.
This milestone does not qualify a vendor-authored source round trip.

## Usage and publication boundary

Supply the actual absolute Windows `.SLDPRT` locator and creation epoch when generating a candidate.
Keep the candidate in research storage until separate native measurements qualify it.
Candidate generation does not set native acceptance flags.

For public SDK output, supply `values["solidworks_native_measurement"]` with its exact `written_at` and parsed `receipt`.
The report must match SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` and its pinned executable digest.
It must also bind the exact archive digest, byte count, healthy controls, edit, clean save and fresh reopen.
The caller establishes the provenance of this unsigned report.
The SDK checks its structure and exact bindings without launching CAD or reading report files.

See the [existing measured publication procedure](../../Solidworks/Construction/SolidworksMeasuredPartPublication.md).
Named binary streams must be empty and seekable at position zero.
The [Windows locator gotcha](../../../Gotchas/Research/Workers/Verification/SolidworksMeasuredWindowsLocator.md) explains receipt checks with streams.

## Verification and limits

The [publication integration check](../../../../tests/Research/EncoderSolidworks/PublicationTests.py) starts a separate Python process.
It replays the two existing historical measured neutral requests through registry and direct public stream writes.
The [process harness](../../../../re/solidworks/EncoderBoundary/CheckPublication.py) blocks file, process, network, native-library and registry access during writing.
It checks changed model, epoch, locator, build, control and reopen evidence, plus a missing receipt.
Each refusal must preserve caller bytes and cursor position.

The check passed locally with Python 3.14.6 and zlib `1.3.1.zlib-ng` on base `66d4f5b856833833bbf67fe62a61c3450d8dc76f`.
The [recorded result](../../../../re/solidworks/measurements/2026/EncoderPublicationBoundary.json) binds the harness and production source digests.
It records four accepted historical stream publications and twenty-eight preserved-stream refusals.
Runtime external-access attempts and native launches were both zero.

| Historical case | Archive bytes | Exact archive SHA-256                                              |
| --------------- | ------------- | ------------------------------------------------------------------ |
| Skew            | 9289          | `67c0a671254fe916f9c0d97a45bd786e32e54f7eb527c78bfe4356079a47d36a` |
| Step            | 9395          | `735b53c173fdcc039ad93873f02c23498edee2df909c83660f9b5c6c8041b282` |

The complete-suite integration module passed locally: `1 passed in 8.02s`.
Run it through the existing merge-queue planner and shards for candidate acceptance.
No separate workflow or runner is introduced.

These checks establish deterministic codec and SDK boundary behavior only.
They do not supply new native measurements or qualify held-out encoder candidates.
The locally inventoried build `34.4.1.1011` differs from the public gate's required build.
No production build identity, receipt requirement or CAD success criterion is relaxed.

The full [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md) remain mandatory.
Fresh-process native controls, body and mass measurements, feature-tree comparison, edits, rebuild, save and reopen remain required.
