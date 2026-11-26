# Fusion decoder and receipt efficiency

The strict Fusion document reader reuses metadata and bulk record spans from container validation.
It constructs each segment's foreign owner targets once and shares them across the other segment profiles.
Each profile still checks its own owner namespace and references.

The pinned research reader parses the canonical neutral JSON once for typed reconstruction and receipt evidence.
It validates both documents and compares the rebuilt JSON bytes with the original canonical bytes.
Use the existing pinned reader options described in the [Fusion reader guide](../../../../Reference/Research/FusionResearchReader.md).

## Verification

The comparison uses committed inputs from corpus revision `74a0bc353421c25f7a6c539897baadf593a05766`.
The manifest SHA-256 is `905b547f47e6b649b190bee11964067ce8dfa81ec8d43fd15e1c37f8d6eda05c`.
The code baseline is `14570404846c8aa1f90b02e68d6f70a419719ca7`.

The independent replay checked both fallback settings on eight inputs.
It matched six strict successes, three partial successes and seven refusals.
The inputs cover three strict controls, reserved F3D and F3Z inputs, and two malformed archives.
The replay matched exact neutral and receipt bytes with the same receipt identity.
Production receipts continue to report the actual SDK and tool revisions.
All three ordered native profiles matched, including repeated object IDs in different segment namespaces.
The independent replay was repeated on `a5cfc64877d3be134337e5aed4adfa189346118a`.

Seven existing native document, configuration and pinned reader process checks passed on Windows with Python 3.14.6.
Nineteen existing container, native document and configuration checks passed on the repaired code.

## Profile

The exploratory strict profile separated native reading, original validation, typed reconstruction, both serializations and receipt generation.
Typed reconstruction took 1,739 to 1,803 ms across three strict inputs in that run.
Parsing the neutral JSON took 26 to 28 ms once per parse.
The receipt path now removes one of those parses.

## Timed comparison

The candidate code revision was `a5cfc64877d3be134337e5aed4adfa189346118a`.
The host was Windows 11 build 26200 with an Intel Core i9-10900 and CPython 3.14.6.
The comparison used strict mode with fallback disabled, BRep enabled, and tessellation enabled.
It collected four warm samples per input and revision across two fresh processes per revision.
Process order was baseline, candidate, candidate, baseline.

| Pinned input       | Native read (ms) | Projection and dispatch (ms) | Neutral encode (ms) | Receipt (ms)  | Whole asset wall time (ms) |
| ------------------ | ---------------: | ---------------------------: | ------------------: | ------------: | -------------------------: |
| Ordinary rectangle |      88.9 → 81.8 |                  62.1 → 59.0 |   2,115.0 → 2,083.5 | 271.6 → 241.7 |          3,179.6 → 2,537.0 |
| Drafted extrusion  |      72.3 → 82.4 |                  75.2 → 77.1 |   2,045.6 → 2,033.8 | 238.3 → 202.9 |          3,041.0 → 2,440.3 |
| Multiline comment  |      90.0 → 96.2 |                  78.0 → 59.1 |   2,136.5 → 2,140.9 | 249.0 → 214.7 |          3,129.9 → 2,559.8 |

Each cell gives the baseline median followed by the candidate median.
Receipt medians fell by 11% to 15%.
Whole-asset wall medians fell by 18% to 20%, and process CPU medians fell by 1.5% to 2.5%.
Whole-asset wall time includes durable output writes and their variable latency.
Git loading, process startup, warm-up, and verification hashes are outside the timed interval.
Native read medians were mixed.
The retained segment indexes are released before auxiliary decoding.
Peak memory and complete batch throughput were outside the measurement.

| Pinned input       | Source SHA-256                                                   | Neutral SHA-256                                                  | Fixed-identity receipt SHA-256                                   |
| ------------------ | ---------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- |
| Ordinary rectangle | 09980af5a2c9e03e0fc9246ed0b20e796c8f5574c8838d255c85bdd08ea1aa9c | 15e49b5f267f2327fd7b69dd975038d9bfa0c25eace57f0a2bcec698e3175825 | c4381b700371626fa1af1846fc6c59307227f1509037f05b9b3dc6c7619315a4 |
| Drafted extrusion  | 8745a3c1396959165517d872f70078377411273cd7f5bcb1870554fc613785fa | 3601ca1c50b43867af3fb08afdab1f84e994994f63913797f2fd920f8b703d2c | a20d45b6131df6ee2e3d95b7f110c6721007deae4182ac3341983450a12bcf62 |
| Multiline comment  | e772cade3e2cdc66aaff829d967b68bb5d9a864c0af0c81fffef0573c6044c62 | 3fe1f829fb2b0a5799ceb0394ce42c143a6907a84ceaece73b48ad1801d4b1c1 | 10537660b0e3fc6d62f5854e7d7e18ec5a2a1a4d53b41c7caedc8cd6a5ea015d |

All timed runs produced the listed neutral and receipt hashes.
The raw timing record SHA-256 is `51ac88d0868afc27bed6ffede9c05a1c23f3268803a32981b925db2482728929`.

The performance and compatibility evidence applies to offline decoding.
Native application acceptance and semantic qualification remain separate.
