# Fusion decoder and receipt efficiency

The strict Fusion document reader reuses metadata and bulk record spans from container validation.
It constructs each segment's foreign owner targets once and shares them across the other segment profiles.
Each profile still checks its own owner namespace and references.

The pinned research reader parses the canonical neutral JSON once for typed reconstruction and receipt evidence.
It validates both documents and compares the rebuilt JSON bytes with the original canonical bytes.
Use the existing pinned reader options described in the [Fusion reader guide](../../../Reference/Research/FusionResearchReader.md).

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

Seven existing native document, configuration and pinned reader process checks passed on Windows with Python 3.14.6.

## Profile

The exploratory strict profile separated native reading, original validation, typed reconstruction, both serializations and receipt generation.
Typed reconstruction took 1,739 to 1,803 ms across three strict inputs in that run.
Parsing the neutral JSON took 26 to 28 ms once per parse.
The receipt path now removes one of those parses.

The performance and compatibility evidence applies to offline decoding.
Native application acceptance and semantic qualification remain separate.
