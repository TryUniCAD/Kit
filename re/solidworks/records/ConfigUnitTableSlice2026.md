# Ordinary SOLIDWORKS configuration unit-table reader

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-UNITS` |
| Owner | PR #121 takeover team |
| Delivery | Main-target branch `codex/solidworks-config-unit-tables` |
| Base | `57f519c9851ef8f4aacd7472f86f5ecaf7bd163e` |
| Prerequisites | [Object maps](ArchiveObjectMapSlice2026.md), [body values](BodyValueSlice2026.md) and [counted rows](CountedBodyRowSlice2026.md) |
| Exit | Complete typed record and map observations, scoped refusals, queue execution and exact revision review |

## Field and map ownership

The ordinary version-19000 unit layouts come from the current
SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` configuration field ledger.
The supported `moUnitsTable_c` is schema one. It inherits the
`su_CObArray` count and contains 16 concrete unit rows. Each row
inherits the recorded `moUserUnits_c.Serialize` field order. Its
specific native suffix follows that base and uses the same field scope.
The density row reads its unsigned one-byte presence field. The
current observed table profile stores zero in that field. The length
row has a separate node field that can bind a distinct length override
allocated within the table. A native-class map reference shares the
descriptor and opens a new object body.
[Pinned configuration field order](https://github.com/TryUniCAD/Kit/blob/8302c824a15830b837c72db75f79cabe5693d200/re/solidworks/records/ConfigBodyGrammar2026.md)

The codec takes a bounded object buffer and a typed map snapshot. It
clones the map membership and consumes the complete buffer through the
shared archive cursor. The table, the concrete rows and the optional
length override may open bodies only in their respective scopes. The
post-read checks validate row order and allocation even when a reused
tag bypasses a body callback. A successful result exposes the original
inherited entries by identity and the newly allocated objects.

The measured field order, scalar widths, class roles and map behavior
are confirmed for these disclosed controls. The user-facing semantics
and legal domains of the stored unit words are partial. Full
configuration parsing, neutral units projection and native writing
require further qualification.

## Disclosed process evidence

The native-authored ladder part retains its length override. The
separately generated concave part has prior native observations and
supplies two different unit tables. These are existing tracked CAD
fixtures. Exact original file and configuration digests are checked
before selecting the typed owner's measured offsets. The offsets and
fixture hashes stay in the research verifier.
[Ladder author and version evidence](../measurements/2026/ReverificationCountOwners01.json)
· [Concave control provenance](../measurements/2026/LocalImportReadbackFixtures01.json)

| Control | Owner and Config-0 interval | Bytes | Map counter | Length fields `f0c`, `f18`, `fb0` | Angle and system `fb0` |
| --- | --- | ---: | --- | --- | --- |
| [L1](../v2026/corpus/ladder/L1_boss.SLDPRT) | `moPart_c.f9b8`, [925, 2412) | 1,487 | 8 to 43 | 2, 0.1, 0 | 0, 4 |
| [ConcaveOwned](../v2026/corpus/local-import-readback/ConcaveOwned.SLDPRT) | `moPart_c.f9b8`, [278, 1699) | 1,421 | 8 to 42 | 4, 0.01, 0 | 0, 4 |
| ConcaveOwned | `moPart_c.f9c0`, [19392, 20447) | 1,055 | 60 to 77 | 4, 0.01, 2 | 3, 1 |

The ladder root occupies slot 9 and its length override occupies slot
12. ConcaveOwned's second root occupies slot 60 and reuses all 17 class
descriptors from the first table at their actual slots. Each decode
executes 19 layouts and the existing `Array`, `Node`, `Scalar` operations
plus the new `Base` and `Present` handlers.

An [independent fixed-width projection](../../tooling/sw2026/ReadWireUnitFields.py)
reads all 13 inherited scalar fields on every unit row, each concrete
suffix and every field of the nested length override from the native
bytes. It walks the tags and class slots with its own counter and checks
the concrete body offsets and full cursor. Each queue case pins the
complete projection's SHA-256. The ladder and linked concave
observations have their own process cases and share one process runner.

The process rejects truncation, trailing data, the wrong archive
version, a density override, an earlier root alias, a null row, the
wrong first-table counter, a wrong length owner, a missing class seed,
and a class slot occupied by an object. No CAD processes launch.
The reproducible process evidence is separate from the queue run.

```sh
python -I -B re/tooling/sw2026/CheckUnitTables.py ladder
python -I -B re/tooling/sw2026/CheckUnitTables.py concave
```

[Exact host receipt and source manifest](../measurements/2026/ConfigUnitTableReader01.json)
· [Ladder queue case](../../../tests/Convert/Solidworks/Configuration/UnitTableTests.py)
· [Linked queue case](../../../tests/Convert/Solidworks/Configuration/UnitTableLinkTests.py)

## Remaining Config-0 work

The observed three native full-configuration records use 142 physical
layouts and 21 field operations. This slice supplies the 19 unit-table
layouts and the two shared field handlers. Relative to its base, the
ordinary aggregate read dependency contains four groups of new files.
Counts below describe the existing aggregate import graph after
excluding the optional part-equation relation mode. Three already
present shared reader modules also have executor changes.

| Dependency group | Paths | Lines | Boundary |
| --- | ---: | ---: | --- |
| Unit layouts and presence executor | 3 | 140 | Included here with the two existing executor edits and guarded table entry |
| Other body operations and expressions | 29 | 725 | Conditional branches, native flags and virtual dispatch, repeat sizing and raw versus runtime words |
| Configuration layout owners and registry | 32 | 4,387 | Model sections, annotation defaults, material and light owners, view and property records |
| Complete model boundary and context | 15 | 400 | Exact ModelHeader object aliases, section bounds, direct owner and cache handlers, final link checks and cursor exhaustion |

A later main-target codec must validate both root sections and their
record traversal before physical configuration admission can depend on
it. The optional equation mode and its resolved sketch dependency
have a separate scope.
