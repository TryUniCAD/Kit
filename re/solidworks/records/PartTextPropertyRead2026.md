# Ordinary part text properties through the SDK reader

Task B04-SW2026-PARTPROPS-READ, owner `/root/assembly_occurrence`, delivery PR #121.
Dependencies are the [measured property owners](PartPropertySources2026.md),
[SDK property vocabulary](SdkPartTextProperties2026.md), actual typed CMgr
configuration nodes, and the ordinary version-19000 archive codecs. The exit
condition for this slice is an exact, visibly qualified public projection of
the disclosed compatible property profile. Complete property conversion,
other property variants and advanced manager construction remain open.

## Public projection and admission

The normal `open_document` part route attaches authored summary fields under
`metadata["document_summary"]`, document custom text under
`metadata["custom_properties"]`, and each actual configuration's custom text
under its own `attributes["custom_properties"]`. Summary names are `title`,
`subject`, `author`, `keywords` and `comments`. Native save author and time
fields remain separate from these authored fields.

`metadata["solidworks.part_text_properties"]["status"]` is `complete` only
after all present scopes pass. The measured UTF-8 XML profile has two identified
sections, correct reserved rows, a bijective PID/name dictionary, TypeID 0,
false equation state, and nonempty single-line literal `vt:lpstr` values.
Document evaluated text must match the literal. A configuration may omit
that duplicate or provide one equal value. Links, other variants, duplicate
identities, malformed XML and unqualified structure reject the projection.

The configuration filename supplies a native configuration ID. Its actual
typed CMgr node and name must equal the configuration exposed by the normal
reader. Neither active position, an English default name nor feature order
substitutes for ownership. All five positive files use ID 0 and the actual
name `modeled default`. Multiple-configuration native qualification is still
open; the implementation checks each present ID independently and refuses
orphan or stale owners.

An absent or empty compatible `Contents/CusProps` manager is admitted. The
empty manager has its own ordinary map starting at 1, concrete schema-one
`moCusPropMgr_c` root, `i32 f0c`, `i32 f08`, keyed `u32 n20` rows and current
`u8 f54`. The measured empty policy tuple is `(-1, 0, 0)` for
`(f0c, f08, f54)`. This is a narrow read-admission profile, not a universal
constructor constant. The [empty advanced owner profile](PartEmptyAdvancedProperties2026.md)
extends admission to the verified keyed file and cut-list owners with no
values. Populated or different policy owners remain guarded.

Unsupported optional properties withhold all three new text scopes and add
the information diagnostic `solidworks.part_text_properties_unavailable`.
The status records the exact reason. Geometry, history and the existing
native reader result remain available. Callers qualifying property support
must require `complete`; an ordinary geometry read alone is insufficient.
Files without these property streams retain the prior path without a new
property status.

## Typed configuration cache grammar

The original pinned `sldmodu.dll` has SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`,
image base `0x4b140000`. The `moCustomProperty` constructor at `0x4be5ef30`
installs vtable `0x4d037160`. Its descriptor at `0x4dae6940` reports a
64-byte object and schema word `0x80000001`. Vtable slot `+0x28` selects
`Serialize` at `[0x4be5f880, 0x4be5fdaf)`, whose 1,327-byte body has SHA-256
`ed49c2315eed3dac83ad61a3b1089d4449b2d90e3b9623c299d98854c05a6182`.
Original PE exports, runtime pointers and `.pdata` boundaries were inspected
with Apple LLVM. No vendor listing or binary is committed.

| Store order | Wire owner | Type | Load gate | Bound meaning |
| --- | --- | --- | --- | --- |
| 1 | `f08` | CString | Current base path | Name output of `getProperty` |
| 2 | `f10` | CString | Current base path | Localized type caption output |
| 3 | `f18` | CString | Current base path | Stored text output; can be stale |
| 4 | `f2c` | i32 | Version >= `0x8f5` | `setEditingAllowed` stores here |
| 5 | `f28` | u32 | Version >= `0xadf` | Type discriminator; 0 maps to API text 30 |
| 6 | `f20` | CString | Version >= `0x12c7` | `setEvaluatedValue` targets this string |
| 7 | `f34` | i32 | Version >= `0x17f2` | Optional integer output; policy semantics remain separate |
| 8 | `f38` | i32 | Version >= `0x1822` | Optional integer output; policy semantics remain separate |
| 9 | `f3c` | i32 | Version >= `0x186e` | Current serialized state; not projected as a text value |

The existing SDK ordinary graph context admits version 19000 only. It now
walks these nine embedded fields inside `moCustomPropertyList`; it does not
enable old-version interpretation or a new tagged object profile. The
CString store/load imports are `0x4cd3da28` / `0x4cd3da30`, signed scalar
store/load `0x4cd3d880` / `0x4cd3d888`, and unsigned scalar store/load
`0x4cd3da60` / `0x4cd3da68`. The serializer reads the file-version context at
`+0x7c0` for its load gates.

`getProperty` occupies `[0x4be64f50, 0x4be6501b)`, SHA-256
`b6fa3987721dbfed6e5349e7a70ef7f715eafb8a6ed22493c9f651d8fdb03d89`.
It exposes the three leading strings, `f2c`, mapped `f28`, `f20` and optional
`f34` / `f38`. The mapped type values are 0→30, 1→64, 2→3, 3→11,
otherwise -1. `f2c == 1` is therefore not the API text type.

`moBaseConfiguration_c::getMoCustomProperties` at
`[0x4b287c80, 0x4b287c88)`, SHA-256
`85933fd474d292ffce785eb51c0ec0dfe31df8b28aee0040b8a8e90e9ba567f2`,
returns the owned pointer stored at `+0xb68`. The wire list is embedded;
the memory member is a pointer. The shared `setEvaluatedValue` entry at
`0x4b2ad5a0` advances the receiver by `0x20` before string assignment, and
`setEditingAllowed` at `0x4b294390` stores the supplied integer at `+0x2c`.
Folded export labels do not change these selected-entry bindings.

## Live values and stale cache

The generated files have empty `fb68` lists but populated configuration XML.
After native editing, the saved polygon cache still contains
`Use the narrow profile`, while its live XML and independent native `Get6`
return `Configuration-only revised B6`. The circle cache similarly retains
`Revised configuration`, while live XML and `Get6` return
`Variant C11 <finished>`. Consequently `fb68` is decoded and retained for
archive ownership and exact serialization, but never supplies live property
values or an unconditional XML-equality gate.

[Cache lifecycle gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Properties/ConfigurationPropertyCacheCanLagXml.md)

## Reproducible proof and limits

Run the source-only [disclosed audit](../../tooling/sw2026/CheckPartTextReading.py)
with the checkout, declared disclosed root and an unused output directory.
Its [fresh-process probe](../../tooling/sw2026/ReadPartTextProbe.py) uses the
normal SDK part entry point and separately round-trips the complete CMgr
stream. Expected values come from the original neutral requests or the
independent native API records, not the XML parser under test.

The [sanitized receipt](../measurements/2026/PartTextPropertyRead01.json)
binds five positives and the actual advanced rectangle negative. Each input
is immutable and identified by hash. The advanced negative preserves its
19 modeling rows, one sketch and three parameters, withholds unqualified
text and exposes the information diagnostic. Three integration tests add
18 fresh public reads across ordinary text, stale cache, absent properties
and fourteen malformed or stale-owner negatives. All negatives retain the
baseline sketch, parameters, bodies and history.

These are disclosed SDK reader and exact grammar proofs. The earlier native
property lifecycle remains separately bound to its own writer snapshot.
This tranche launches no native process, changes no writer bytes or public
writer admission, reads no held-outs, and claims no complete property-family
or arbitrary-configuration acceptance.
