# Retained native assembly bytes do not establish complete conversion

A CATProduct can decode into a structurally valid `CadDocument` with no feature
timeline while preserving its original container in `brep_payloads`. Copying
the product without its companion parts leaves component references unresolved.
The CATIA reader also marks native-only transforms and constraints explicitly.
The interchange JSON writer can serialize all these records successfully;
that does not establish complete component geometry or portable assembly behavior.

`kit convert` now refuses retained payload records of every role, including
verification records or records whose inline data is absent. It also refuses
explicit native B-rep geometry and missing or explicitly unresolved assembly
records. The same checks traverse nested component documents. Changing the
source's filename, format-ID spelling, or JSON payload role does not qualify
the retained bytes for conversion. Complete embedded/local typed reference
representations remain eligible for normal writer policy checks.
An assembly root or subassembly can record a `source_path` solely as provenance
while its actual representation is a local child-instance graph. Such owners
need no separate embedded document or body/mesh link. The guard recognizes these
local owners and still checks every descendant for missing links or explicit
unresolved state.

Use `kit decode` or the deterministic research tools to inspect these artifacts
while their semantics are recovered. The public SDK and CATIA reader are unchanged.
See [the guard](../../../../src/convert/Commands/CheckPortable.py),
[the isolated CATProduct process cases](../../../../tests/convert/Commands/CliCatiaTests.py),
and [the change entry](../../../Changes/Commands/OpaqueConversionGuard.md).
