# Replay prepared SOLIDWORKS constructor JSON in a fresh process

## Behavior

The [replay integration check](../../../../tests/Research/EncoderSolidworks/JsonReplayTests.py) exercises the separate source-admission and candidate-generation stages.
It uses `prepare_generation_input` and `generate_prepared_candidate` from the [research adapter](../../../../re/automation/EncoderRoundTrip/Solidworks.py).
The [existing encoder entry](SolidworksEncoderRoundTrip.md) defines the bounded part family and native acceptance requirements.

The parent process constructs each cold source in memory and reads it through the strict SDK.
It admits the source, applies the requested depth edit and serializes the ordinary typed constructor request to JSON.
The request retains source provenance, but has no native archive, B-rep, native payloads or wrapper metadata.

A new isolated Python process receives only that JSON, locator and epoch through standard input.
It imports the required modules and text codecs before generation begins.
During generation, an audit hook refuses file access, process launches, sockets, native-library loading and registry access.
A process profiler also refuses any call back into source admission or reconstruction.
The child must reproduce the parent candidate digest.
It must also reject inconsistent feature and parameter depth values, plus extra metadata.

## Usage

Use a trusted checkout with the new adapter API and the four committed authored requests and native envelopes.
Run the check with the pinned Python environment.
Select a new output filename when recording evidence.

```powershell
python re/solidworks/EncoderBoundary/CheckJsonReplay.py --root . --output ReplayEvidence.json
```

The command emits its result as JSON.
The optional output contains the same evidence, including method and source digests.
The [process harness](../../../../re/solidworks/EncoderBoundary/CheckJsonReplay.py) writes no native source file.

## Verification and limits

The [recorded evidence](../../../../re/solidworks/measurements/2026/EncoderRoundTrip/JsonOnlyReplay.json) passed on Windows AMD64 with Python 3.14.6 and zlib-ng `1.3.1`.
All four fresh children reproduced the exact measured digests.
The baseline and independent held-out profile each passed at reconstructed and edited depths.
Each child rejected both unsupported mutations.
External-access attempts, source-admission calls and native launches were all zero.
The complete integration test passed locally: `1 passed in 16.04s`.

| Case                    | Archive bytes | Exact measured SHA-256                                             |
| ----------------------- | ------------- | ------------------------------------------------------------------ |
| Baseline reconstruction | 9338          | `32df941b3ded7b94cbd6ee4f2935331c5147569387b5b3870b9d8ac289b08999` |
| Baseline edited         | 9288          | `38fe98ae5975626a6362f1a1ae72a030a7d78a18c4fdc36db64dd35938232f33` |
| Held-out reconstruction | 9462          | `0a58250e2c1aaaf717b5a6414656f622a9abba3d54ee9ca44b9120a7b04884d9` |
| Held-out edited         | 9406          | `d670154e2eca290eba02440d24b28ac1ca11f0ef390aa01c7668909fba930bfd` |

On the recorded compression runtime, a measured-digest mismatch fails the check.
Other runtimes must preserve exact parent-to-child replay, but their result identifies any mismatch with the measured archive.
Matching inflated streams alone does not qualify another complete archive digest.

This evidence establishes deterministic JSON-only generation and explicit refusal of unsupported prepared requests.
It does not add native measurements or qualify additional source families.
The existing exact receipt requirement still controls public SDK publication.
The new test uses the existing complete-suite planner and shards.
No workflow or runner is added.
