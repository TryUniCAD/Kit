# D01 assembly stamp and empty configuration bookkeeping

Task `B04-SW2026-MATES-CONCENTRIC/source-stamps` in PR #121,
owner `assembly_frontier`. The proof starts at
`5ccf707ad3e82eb409d33833ba013e79b93ca84a` with the corresponding
assembly dependencies in aggregate
`9eb5a40b67406ea9b5a306e3cc5074d013096e66`. It uses the recorded
SOLIDWORKS 2026 SP05.2 `34.5.2.0604` disclosed D01, D02 and D03
source and edited parents. The exit for this increment is a generated
copy of the three observed bookkeeping forms from their actual owners
in the existing neutral construction. [Property baseline](ConcentricD01PropertyOwners2026.md) ·
[CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)

## Confirmed ownership in the disclosed scope

| Stream | Actual fields and source |
| --- | --- |
| `ModelStamps` | Exactly three little-endian unsigned 32-bit values. The creation value, model update counter and body counter are the actual `f70`, `f40` and `f44` in both typed headers. |
| `_DL_VERSION_19000/DLUpdateStamp` | The same unsigned 32-bit header update counter and one canonical null object tag. The observed form has no pointer to recreate. |
| `Contents/CnfgObjs` | A zero unsigned 16-bit prefix, one canonical null object tag and two empty Unicode archive strings. This proof covers only the no-override form under a single actual selected configuration. The typed CMgr active, cached and keyed slots all name that same configuration. |

The model creation event is independently established by the actual
root revision log in both headers. The source configuration and save
owner agree with the previously verified property scope. The existing
[configuration serializer finding](ConfigurationProgress2026.md#unfinished-override-persistence)
separates explicitly persisted feature overrides. No populated
override branch is claimed.

| Disclosed case | `f40` source → edited | Root `f1300` source → edited | `f44` both states |
| --- | ---: | ---: | ---: |
| D01 aligned and free | 105 → 106 | 102 → 103 | 101 |
| D02 aligned and locked | 106 → 107 | 102 → 103 | 101 |
| D03 anti-aligned and free | 105 → 106 | 102 → 103 | 101 |

D02 rules out using the root's geometry stamp or the same fixed
increment from it as the display serial. The sums in the assembly
configuration directory also have their own owners. The shared
`EncodePartMeta` constructor already implements these three encodings.
Across the six sources it reconstructs all 18 streams exactly using
only the actual headers, with lengths 12, 6 and 12 bytes respectively.
[Distinct geometry and transform operations](NestedAssemblyReferenceState2026.md#distinct-stamp-operations)

## One new output from the same neutral request

The worker receives the exact JSON used by the prior property proof.
There are no additional field values in that request for these
streams. The emitted chronology, generated header and active
configuration supply their values and owner identities. The worker
routes through the same `EmitAsmStreams` model and shared container
builder. It rejects a missing revision log or a mismatched paired
header before constructing any stamp stream. It validates the complete
new stream inventory and selected owner again on readback.

Two independent stdin-only workers build the same 13,796-byte parent,
SHA-256
`4261559e326f8aba8c0a26bcf201b00583b844ab924fe831d72da3071311c24a`.
All 17 earlier parent streams, including the four property streams,
and the entire generated child remain exact. The parent adds only the
three bookkeeping streams. Its creation epoch is 1795044311, and its
fresh update and body counters come from the current generated header
at 101 and 101. The constructor does not use the source's update counter
106 to initialize the fresh model. Both workers preserve the reciprocal
mate, visual and chronology checks, and record zero external accesses.

Seven explicit refusal cases cover missing log and member, discrepant
header and display counter, trailing configuration data, detached
current configuration and collision with an emitted scope.
[Exact receipt](../measurements/2026/ConcentricD01StampStreams01.json)

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01AssemblyStamps.py \
  --disclosures /absolute/path/to/Oracle121Takeover
```

## Bounds and next ownership

The actual source still refuses `CheckAsmRoot`. The generated parent
has 20 streams, with 23 saved source members outside this proof.
Native construction has not established the historical progression
of `f40` or `f1300`, and this proof leaves both header presence policy
and whole-source admission unchanged. It adds no native or held-out
qualification.

The system XML requires independent mapping of actual preferences.
In the inspected D01 original it has 49 rows. The XML
`SW_UnitSystem=5` and `SW_UnitsForce=3` differ from the binary
unit-system and force enum operands 4 and 2. The standalone
`Contents/User Units Table` parses to 16 concrete roles at terminal
map 36 and agrees with the corresponding model's scalar fields in
that save. A direct copy of binary enum operands into the system XML
would change the meaning. A future comparison should bind complete
embedded and external unit state and establish the XML enum, format
and locale choices separately. Source Biography already replays
through the shared history codec, with two embedded runtime records
per parent. A real authored save lifecycle and its independent
machine observations would be needed to populate those records.
[Biography ownership](HistoryConstruction2026.md)
