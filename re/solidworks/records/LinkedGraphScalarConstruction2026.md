# Shared scalar I/O and linked graph dependency census

Status is a shared fixed-width archive primitive with current process compatibility
evidence. The ordinary Config/Resolved semantic body grammar still has explicit
research dependencies. Scope is SOLIDWORKS 2026 SP05.2, archive version 19000.

## Linked ownership

The standalone model header supplies its actual self and directory file nodes to
the configuration map. Config's final class/object snapshot seeds ResolvedFeatures.
The resulting Resolved snapshot seeds MatesList. Each stage retains the original
header object identities, with indices derived from its actual shared counter.

CMgr starts an independent class/object map at index 1. The resolved reader obtains
model kind from the Config root and obtains `moConfigurationMgr_c.f658` from this
separate manager archive. These inputs control the part MBSM suffix. Reading the
manager supplies context without adding its classes or objects to the Config map.
The resolved read therefore has an actual CMgr source dependency in addition to
its inherited Config map. Its store uses the retained context.

The configuration header load remains a dependency of Config reading. Its source
reader and spans are retained by `model_header_source`. Schema phase totals below
include these executed dependencies, including the repeated CMgr read performed
by the resolved entry point. They count parser operations across the disclosed
batch, with each selected phase identified separately.

[Native map and CMgr context rule](ArchiveMapConstruction2026.md)

[Shared header handoff](ConfigHeaderHandoff2026.md)

## Measured source dependency census

The census used only disclosed A17, A18 and A19 parent/child pairs and their three
frozen generated counterparts. Each file matched its existing source lock or
generated manifest before parsing. All selected Config, CMgr, Resolved and available
Mates streams re-emitted exactly. The independently authored Python census wrapped
the existing registry and primitive callbacks to count executed operations and
record final declaration file, line, hash and provisional classification. It
captured no scalar values or CAD payloads in its report.

| Selected phase | Files | Reached schema union | Executed typed scalar fields | Remaining provisional schemas |
| --- | --- | --- | --- | --- |
| Config load, including model header | 12 | 158 | 45,690 | `su_CMapStringToString` |
| Config store | 12 | 153 | See receipt | `su_CMapStringToString` |
| CMgr load | 12 | 46 | 4,002 | `moContextChainComponent_c` |
| CMgr store | 12 | 46 | See receipt | `moContextChainComponent_c` |
| Resolved load, including CMgr context | 12 | 166 | 27,744 | `moContextChainComponent_c` |
| Resolved store | 12 | 138 | See receipt | See receipt |
| Mates load | 6 | 69 | 3,847 | Empty |
| Mates store | 6 | 69 | See receipt | Empty |

The direction-specific union contains 299 schemas owned by 32 research source
modules. The scalar operation `Schema.P` accounts for 81,283 calls in the listed
load phases and is the largest executed field-reading operation. The census
records custom operations, repetitions, conditionals, base/embedded calls, actual
raw-operation owners and declared lengths separately. A registry's declared
proof status and an executed usage-profile admission retain their distinct fields.
The census supplies source provenance and actual reachability for this batch.
Per-field native meaning and construction rules remain in their individual ledgers.

## Shared representation rule

The SDK scalar vocabulary is the standard little-endian integer and IEEE floating
representation already used by the existing Core primitive implementation.
Each name determines its width and signedness independently from the field value.

| Kinds | Bytes | Representation |
| --- | --- | --- |
| `u8`, `i8` | 1 | Unsigned or signed 8-bit integer |
| `u16`, `i16` | 2 | Unsigned or signed 16-bit integer |
| `u32`, `i32` | 4 | Unsigned or signed 32-bit integer |
| `u64`, `i64` | 8 | Unsigned or signed 64-bit integer |
| `f32`, `f64` | 4 or 8 | IEEE binary32 or binary64 |

Unsigned integer values occupy `[0, 2**bits)`. Signed integer values occupy
`[-2**(bits-1), 2**(bits-1))`. The same Python `struct` conversion and range checks
apply to encoding. Generic callers retain supported boolean and numeric-protocol
conversions. The SDK header's existing integer validation continues to reject
boolean fields before encoding. Floating wire representation receives the existing
Python `struct` behavior, including nonfinite values. Semantic coordinate or
parameter validity belongs to its enclosing native owner.

The current corpus directly exercised eight primitive kinds. The signed 8-bit
and signed 64-bit vocabulary retains the previous generic codec implementation's
representation. This migration supplies no new native owner or acceptance claim
for an unexercised kind or archive mode.

The existing 2026 geometry proof binds unsigned-byte, unsigned-long and double
reads to the actual `swccu.dll` input-buffer operations and confirms their
one/four/eight-byte widths on the pinned little-endian x64 build. Other native
owner ledgers state their field widths. This change reuses those declared
representations and the established Core grammar.

[Native primitive and geometry proof](GeometryArchive2026.md)

[Unsigned note count and owner-specific signed interpretation](AnnotationArchive2026.md)

[Scalar vocabulary](../../../src/convert/adapters/solidworks/Archive/Scalars/ScalarWords.py)

## Actual loader integration

`Core.Load.prim` delegates to SDK `ReadScalar`. Its cursor advances only after
successful decoding, and a short read retains the existing `ArchiveError`
diagnostic and position. `Core.Store.prim` obtains encoded bytes from SDK
`EncodeScalar` before mutating its buffer. A packing failure leaves that buffer
unchanged. Load's existing conversion to immutable bytes remains at its input
boundary, preserving its accepted input buffer types.

The SDK header field decoder uses `ReadScalarMut` on its existing bounded cursor.
The cursor's `TakeBytes` preserves its prior truncation validation and diagnostic.
Header field encoding uses `EncodeScalar` after its existing field validation.
Header format-code aliases and the shared scalar vocabulary supply identical
widths to bounds flags and the existing layout. Integer signedness, field names,
object identity, map snapshots and all schema control flow retain their owners.

FieldScan and its permanent assertion fingerprint all scalar source modules.
The schema source proof also records those modules and the header selection/version
dependencies. The header audit binds its new scalar reader dependencies.
The production modules contain no research imports or file/native dependencies.

## Verification and admission boundary

Five real assembly process integrations passed locally in 8.41 seconds under
Python 3.11 and pytest 9.1.1. They include the guarded generated distance pair,
synchronized sources and empty/single/repeated construction. Two malformed
generated containers fail through the real header CLI. One truncates the final
ModelHeader scalar, and one leaves only three bytes of the MatesList i32 prefix.
Both fail at their expected scalar boundary and publish no success report.

The six disclosed/generated pair comparisons passed all 12 Config/Resolved
handoffs and 24 standalone header comparisons. Their six typed projection CLI
outputs remained byte-identical to the pinned earlier implementation. The generated
distance child's linked field inventory passed strict schema admission, and the
permanent source assertion verified 92 implementation fingerprints. Black, Ruff
0.17.4, Mypy 2.4.1, Pyright 1.1.414 and the steering checker passed the ten scoped
SDK/test files. Pyright printed its three existing unsupported-setting notices.

The receipt preserves the pre-migration census revision and original private
report hash separately from the final codec/source hashes. Its reconstruction
contains only independently authored metadata. No held-out CAD payload or native
application execution contributed to this migration. The two named provisional
schema dependencies and the remaining production body-grammar promotion still
govern public linked-graph admission. Oracle and held-out acceptance remain the
next evidence requirements for a complete native conversion claim.

[Source census and migration receipt](../measurements/2026/LinkedGraphScalarCensus01.json)

The governing criteria state “There are two acceptable stopping conditions.
The first is success under every criterion on this page. The second is the end
of the available context.”

[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
