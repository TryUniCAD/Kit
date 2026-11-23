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

The performance and compatibility evidence applies to offline decoding.
Native application acceptance and semantic qualification remain separate.
