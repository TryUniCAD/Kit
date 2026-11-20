# SOLIDWORKS 2026 configuration directory codec

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CMGR-HEADER` |
| Owner | PR #121 takeover team |
| Delivery | Main-target branch `codex/solidworks-configuration-directory` |
| Prerequisite | [Counted rows](CountedBodyRowSlice2026.md) and [body values](BodyValueSlice2026.md) through [PR #177's preparation revision](https://github.com/TryUniCAD/Kit/commit/453a944a0e0bcc1539496a5a62ae1aadefe3db63) |
| Exit | Fresh-process explicit graph construction, role refusals, byte and map identity on disclosed controls, review and CI on the delivered revision |

## Shared source closure

The field interpreter uses the shared scope, frame, object, count,
text and scalar handlers. Its dispatch tables select `Scalar`,
`Text`, `Node`, `Array` and `Embed`. The field loops invoke those
handlers directly and retain field path diagnostics. An embed creates
a child field scope and dispatches its declared layout in the same
object body. The common object-list layout owns the list count and
row node fields.

The [aggregate source](https://github.com/TryUniCAD/Kit/commit/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f)
pins 13 source outlines for the shared body steps with manifest SHA-256
`f06f49721dec19d1e653951fa5db37eadb2fa228c5e01cb9f196c52f9706b896`.
It also pins the manager modules, body usage report and common
container layouts with manifest SHA-256
`f943b57c4caf4d5a6166f1a05621f91a62379f7f9920ef3baebfda7575815181`.
The delivery extracts the object-list rule from the container
layouts, narrows the action tables and puts dispatch in the field
loops. The nesting callbacks implement the registered embed rule.
It adds separate manager descriptors and role checks. Nine production
modules match the aggregate byte for byte.

The delivered 23-file production manifest SHA-256 is
`4111213382e0c2cc09cf8e79c4c09c716d7effc5ccd3d400d4d8180d4e4c5b8f`.
Each manifest hashes the sorted repository-relative paths, each
followed by a NUL, the lowercase file SHA-256 and a newline. The
archive dependency walk found no import cycles in 88 modules.

## Native layout and roles

The evidence applies to SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`
and its ordinary version-19000 stream. Native manager and child
store owners are `sldarchiveu.dll!0x319f7270` and `0x319f6d90`.
Their native descriptors at `0x31a24090` and `0x31a240c0` give wire
schema one. The manager starts a map at one and opens its body with
`dmConfigMgrHeader_c`. Its `f08` embeds `suObList`, which stores an
ordinary vendor count and the `dmConfigHeader_c` objects. The
manager then stores `f60` as a `u32` and `f68` as an `i32`.
The child stores nine scalar words and four CStrings. The
legacy manager list at `f58` is absent at this version.
[Exact native manager and child rules](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/ConfigurationManagerHeader2026.md)

Native construction appends a concrete configuration header.
The read callback checks the root and leaf class roles before reading
their fields. The row check covers nulls and references that skip the
body callback, and also runs before writing. The reader and writer
retain a structural alias to a valid mapped child. Native directory
controls have one concrete child each. The repeated alias case is
independently framed for the shared graph contract.
[Role and traversal gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Configuration/ManagerHeaderRolesConstrainTraversal.md)

This layout has at most two open object bodies. Its one embed and
array contribute fixed additional frames and the rows run
sequentially. Recursive arrays of tagged nodes in other layouts
accumulate field and schema callbacks at each level. Their depth
contract needs separate verification when those layouts are admitted.
[Counted callback stack boundary](BodyValueSlice2026.md#counted-callback-stack)

## Disclosed controls

A container-only inventory verified the file hashes, format 4 and
archive version 19000 of both controls. Their logical directories
start with a schema-one manager declaration, a one-row short count
and a schema-one child declaration. The map starts at one.
The expected snapshot has class and
object entries 1–4, root slot 2, child slot 4 and next index 5.

| Input | Origin | File SHA-256 | Directory SHA-256 |
| --- | --- | --- | --- |
| [L1](../v2026/corpus/ladder/L1_boss.SLDPRT) | Disclosed native-authored part | `55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6` | `caa3cb00d615faa644ca20786ae98ff6a4896237648e90c6ed431694f86bb352` |
| [ConcaveOwned](../v2026/corpus/local-import-readback/ConcaveOwned.SLDPRT) | Disclosed generated part with native observations | `fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33` | `9073ac9c452c912ff17b7e788b0e2f4715c9253eb4032fa3771566f2767c4225` |

Each directory is 137 bytes. The existing
[L1 version receipt](../measurements/2026/ReverificationCountOwners01.json)
and [ConcaveOwned fixture receipt](../measurements/2026/LocalImportReadbackFixtures01.json)
bind the source identities. Exact typed re-emission of these
distinct directory streams awaits remote CI on the delivered code.

## Process exit

The [worker](../../tooling/sw2026/CheckManagerDirectory.py) invokes
the binary codec from a fresh process and publishes only a complete
result. The [row case](../../../tests/Convert/Solidworks/CmgrHeader/ManagerRowTests.py)
uses independently framed bytes for signed and unsigned words,
Unicode text, the embedded list and a concrete child's alias.
The [extended count case](../../../tests/Convert/Solidworks/CmgrHeader/ManagerCountTests.py)
authors 65,535 rows. It checks the first canonical extended count,
class slot 3 reused by distinct child objects 4 and 5, and the
remaining short aliases to child 4.
The [role cases](../../../tests/Convert/Solidworks/CmgrHeader/ManagerRoleTests.py)
use missing bodies to verify early rejection of wrong roles and
schemas. The null and manager-reference cases check both directions.
The [disclosed replay cases](../../../tests/Convert/Solidworks/CmgrHeader/ManagerNativeTests.py)
require complete byte consumption, exact re-emission and matching
map membership.

The binary constructor takes the actual typed directory fields.
`ReadMgrHeader` uses a fresh cursor over its immutable input.
`WriteMgrHeader` allocates its map and output privately. Its object
store assigns map entries, and computed counts stay in the operation's
field scope overlay. The process snapshots input node fields, identities
and position markers across fresh writes and replay.
Production projection from full part and assembly configuration
graphs and container integration have separate acceptance work.
Native document rebuild and edit qualification require their own
oracle measurements.

Scoped Black, Ruff, Mypy, Pyright and steering checks passed. The
donor scan found no recorded payloads across 3,292 production
sources. The process declarations were parsed and their execution
awaits remote CI.
