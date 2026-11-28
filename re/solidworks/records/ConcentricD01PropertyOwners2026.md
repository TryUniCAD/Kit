# D01 concentric assembly property ownership

Task `B04-SW2026-MATES-CONCENTRIC/source-properties` in PR #121,
owner `assembly_frontier`, base
`3b5caa3b599b2184f32260e8b383d15044946d5f`. Both states of D01,
D02 and D03 are previously disclosed and locked to SOLIDWORKS 2026
SP05.2 `34.5.2.0604`. The exit for this increment is construction
of the observed property owner and all three XML scopes through the
same modeled D01 parent that preserves the original assembly chronology.
[CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) ·
[Prior chronology proof](ConcentricD01AssemblyChronology2026.md)

## Actual source owners

| Owner | Confirmed typed scope |
| --- | --- |
| `Contents/CusProps` | Map base 1, schema-one `moCusPropMgr_c`, signed policy `(-1, 1)`, unsigned row count one, file key zero and zero final flags. The scoped `moCusPropContainer_c` owns a distinct schema-one `moAssyFilePropContainer_c` in its first tagged child. That assembly file child has two null tagged slots. Both remaining container references are null and the trailing policy is zero. All six streams are 106 bytes and reconstruct at terminal map 7. |
| `docProps/custom.xml` | Shared empty literal document property form. Its reserved properties and name dictionaries reconstruct exactly in all six 853-byte streams. |
| `docProps/Config-0-Properties.xml` | Empty literal configuration property form, 699 bytes, bound to the actual selected `Default` configuration in CMgr, its only active keyed `dmConfigHeader_c` row and both self-file references. The selected configuration is the same typed object in the CMgr active and keyed slots. |
| `docProps/core.xml` | Three ordered package provenance elements. Each source has its actual last-save actor, the earlier physical package creation instant, and the save instant in UTC whole seconds. The saved modification time equals the self-file save event in both headers in all six cases. The package creation differs from header creation by +1 second in both D01 and D02 pairs and by zero in D03. A common fixed offset cannot model these states. No summary text is authored in this cohort. |

The distinct part file container and its empty cut-list container remain
the owners in all six associated children. The assembly codec refuses
them, and the existing part codec continues to admit them. The research
code uses the shared archive body reader and writer and the established
literal XML rules. The proof establishes the empty assembly child's two
null slots. It leaves nonempty layouts, advanced property lists and
multiple configuration rows unsupported.
[Part property owner contrast](PartEmptyAdvancedProperties2026.md) ·
[Property clock and class gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Properties/AssemblyPropertyOwnersDifferFromParts.md)

## Guarded construction

The source supervisor opens only the named disclosed originals and
their derivatives after confirming their file hashes and prior locks.
It resolves the root and configuration and regenerates each of the four
source streams from typed inputs for exact comparison. The source-only
last-save actor remains in the source comparison. The neutral worker
receives the actual logical package creation event and selected
configuration, with a separate explicit save actor for the generated
package. The new modification value follows the generated Header2 and
ModelHeader self records. It never reads the original Core XML or
takes a source actor, archive class ID or binary payload.

The existing chronology model constructs the parent through
`EmitAsmStreams`. Its new property option is applied to that computed
stream map, checks that the real configuration and both headers own the
requested scope, and prevents replacing any already emitted property
owner. Both fresh stdin-only workers build the same 13,423-byte parent,
SHA-256
`86915e1c4d796a52dd7b6004e57c5ae6b04f16bc070a5204b43532094ab8b18c`.
All 13 original generated parent streams and the full generated child
remain byte-identical, including the signed concentric mate, child
appearance, selected state, revision logs and prior placement history.
The three source property streams with only empty logical values
reproduce exactly. The summary stream retains the independent created
event and uses the new save event and actor. Changing just the neutral
created event and actor changes just that stream. The workers observe
zero external accesses.

The proof refuses a crossed part property class, a foreign
configuration, a competing scope, a future package creation event
and an extra authored summary field. All six exact source replays
are independently checked. [Sanitized receipt](../measurements/2026/ConcentricD01PropertyOwners01.json)

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01AssemblyProperties.py \
  --disclosures /absolute/path/to/Oracle121Takeover
```

The original source still refuses at `CheckAsmRoot`. The new 17-stream
modeled parent leaves 26 source streams outside this proof. The remaining
ledger includes system XML and package application metadata, linked
document state, Biography, source update allocation, Header2 model
presence and the unmeasured native cache inventory. The next bridge needs
scope-checked source inventory handling and native proof that each omitted
cache can be regenerated. The assembler neither advances public eligibility
nor touches H01 or H02.

The [stamp and configuration bookkeeping proof](ConcentricD01StampStreams2026.md)
adds three streams from the same neutral request and retains all four
property owners byte for byte.
