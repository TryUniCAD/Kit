# Ordinary SOLIDWORKS configuration section framing

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-SECTIONS` |
| Owner | PR #121 takeover team |
| Delivery | Separate main-target branch `codex/solidworks-config-section-framing` |
| Preparation base | `fda31a2679995db48aad4fd2ff54d86966fd272d` |
| Prerequisites | [Archive object maps](ArchiveObjectMapSlice2026.md), [body value reader](BodyValueSlice2026.md), [standalone headers](StandaloneHeaderSlice2026.md) |
| Exit | Disclosed source framing, direct identity and empty ghost owner verified in guarded queue processes, malformed inputs refused, and current revision review and CI |

## Native format evidence

For the ordinary version-19000 schema-one `moPart_c`, serialization at
`sldmodu.dll!0x4c229a60` dispatches lightweight and resolved body slots
`+0x4b8` and `+0x4c0` to `0x4c2309d0` and `0x4c2378b0`. Both use the
section helper at `0x4c2114b0`. The helper consumes a little-endian unsigned
32-bit byte count before the section body. The parent stream also has the
root's ordinary class descriptor. The length prefixes allocate no archive
slots. The supported action refuses the alternate section-skip conditions
`0x80000` and `0x100000`.
[Part dispatch and section helper](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/ModelConstruction2026.md#native-archive-dispatch)

The lightweight section begins with `moModel_c.FUN_4c17aa00`. Its first
operation registers the whole ordered model-header reference list in the
live Config map, followed by stored `fb0` (signed) and `fb4` (unsigned).
Registration writes zero bytes and pegs the inherited base after the
selected nodes. The underlying map rule is bound to `sldmodu.dll`
`[0x4c17bd90,0x4c17c6b3)` and `swccu.dll!0x31a39d00`. This extraction
uses the existing `HeaderRefNodes` and `BindNodesMut` rules. The model
root must already exist on the map. Its linked header objects keep
their standalone archive indices and body spans.
[Header context and native call sites](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/ConfigHeaderHandoff2026.md)

In the resolved section, `moModel_c.FUN_4c234150` reads embedded `fd90`
after atom manager `fd88`. `moGhostBodyIdManager_c.FUN_4bf050e0` begins
with signed `f80` then a packed signed 32-bit word. For current archives,
the high four bits are sign-extended into `fe0` and the low 28 bits give
`n`, the count for `objects`. Empty `objects` requires zero row bytes
and introduces no archive map entry. The shared action keeps both values
without clamping or deriving flags from the count. Populated rows and
older layouts require their own evidence.
[Native field order and packed-word rule](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/tooling/sw2026/serial/defs/ConfigPart.py#L182-L197)

## Disclosed observations

The [source manifest](../measurements/2026/ConfigSectionSource01.json)
records the native file, both stream hashes, exact module-build hashes and
pinned original rules. The reference aggregate reader at
`41569e84c090bad1066cda6b64567d8f901768f7` was instrumented in memory
around `Section`, `Direct` and the embedded ghost owner during a complete
read of each tracked source. The section action, model grammar, Config
entry and header selection matched the pinned source at
`f4fc8744235448c0ff6048e4447440bb7927a6d1`. These are the
SOLIDWORKS 2026 SP05.2 `34.5.2.0604` build-bound controls used for prior
Config slices.

| Control | LW length position and body | RES length position and body | `fd90` record and map counter | Stored `fe0`, `n` |
| --- | --- | --- | --- | --- |
| L1 boss | 14, [18, 3052) | 3052, [3056, 25390) | [3174, 3182), 59 to 59 | 1, 0 |
| ConcaveOwned | 14, [18, 2105) | 2105, [2109, 22700) | [2227, 2235), 52 to 52 | 0, 0 |

Both root descriptors occupy [0, 14). Each lightweight section registers
the true model-header self object in Config slot 3 at physical offset 18.
The standalone self indices are 69 and 15. The live Config counter goes
from 3 to 4 and the inherited base from 1 to 4. Both sources store
`fb0 = 0`; L1 stores `fb4 = 19000` and Concave stores `fb4 = 0`.
The archive version used by the reader comes from the container metadata.

## Shared reader and queue proof

`ReadSectSpan` opens an absolute byte window over the original memory
without advancing its parent. The shared `Section` action uses that window
with the same graph and field context. Scalar, tag, descriptor, CString
and count readers honor the active end. A successful action must consume
its body exactly before resuming the enclosing cursor. On failure the
outer cursor is restored. This reader does not make a failed object body
transactional. Its caller must abandon the incomplete graph, since fields
or slots decoded before a later failure are still partial.

The fresh-process worker verifies both native frame declarations,
allocates the actual root and enters its lightweight section through the
shared action. The bounded callback checks the zero-byte direct handoff
against the actual standalone header and reads two model scalar words.
It verifies restoration of the parent cursor when the partial body stops.
It then isolates the hash-bound embedded ghost owner within the resolved window.
Its in-memory audit denies file, process and network access after setup.
The probe deliberately exits its root read without returning a completed
root. Recorded ghost map counters come from the earlier complete reference
trace. The bounded read of each ghost record verifies no map allocation.

An independently authored nested section exercises exact body consumption,
counted objects, absolute offsets and a true object reference after the
section. Malformed cases drive the same process and cover short prefixes,
oversized and unconsumed lengths, a nested section crossing its enclosing
end, scalar and graph frames crossing their bounds, both extended count
dialects, ANSI payload and UTF-16 length boundaries, wrong-version and skip
conditions, inline header roles and populated ghost rows. A signed packed
contrast checks a negative high nibble without adopting it as a default.

```sh
python -I -B re/tooling/sw2026/CheckCfgSection.py ladder
python -I -B re/tooling/sw2026/CheckCfgSection.py concave
python -I -B re/tooling/sw2026/CheckCfgSection.py siblings
```

The independent sibling frame authors 32 bytes from the ordinary tag,
length and scalar rules. It obtains the original L1 header object
through the typed ModelHeader reader. The first section at [18, 22)
registers that exact node in configuration slot 3 and advances the
map base and counter to 4. The later section at [26, 32) resolves an
ordinary object tag to the same node. Both sections complete with the
shared map and the outer cursor ends at 32. The header node retains
standalone index 69 and its original offsets.

With the same authored bytes and an absent header alias, the first
section completes at 22. The second section stops after its tag at 28
with an unresolved object diagnostic. Its failure restores the outer
cursor to 22. Base and counter stay at 3 and slot 3 remains absent.
[Sibling process evidence](../measurements/2026/ConfigSectionSiblings01.json)
· [Sibling queue case](../../../tests/Convert/Solidworks/Configuration/SectAliasTests.py)

The new [guarded process cases](../../../tests/Convert/Solidworks/Configuration/CfgSectionTests.py)
await the merge queue. Complete section-body traversal still needs the
remaining model owners, including visual properties and native view context
operations. The version-19000 layout does not enable older skip variants,
populated ghost rows, public Config admission or any writer.

[CAD acceptance criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
