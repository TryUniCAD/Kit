# Ordinary SOLIDWORKS configuration field actions

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-FIELD-ACTIONS` |
| Owner | PR #121 takeover team |
| Delivery | Main-target branch `codex/solidworks-config-field-actions` |
| Preparation base | `391bec82992173dd582efed6f042074a10aea29d` |
| Prerequisites | [Typed body values](BodyValueSlice2026.md), [unit tables](ConfigUnitTableSlice2026.md), [relation and color members](ConfigMemberFieldsSlice2026.md) |
| Exit | Bounded native records, inherited map identities and malformed frames through the queue process cases, followed by exact revision review |

## Field and owner rules

This slice extracts read-side branch selection, concrete virtual dispatch
and fixed 16-byte fields from aggregate
`f4fc8744235448c0ff6048e4447440bb7927a6d1`. The sketch and exploded
view managers descend through ordinary version-19000 feature fields.
The shared feature layout, fixed-width handler and virtual lookup retain
the aggregate implementations. The branch and virtual readers select
the smaller subset needed by these owners. A virtual flag must resolve
to a Boolean. A plain virtual must resolve to a named layout or a
declared empty target. Undefined slots and unsupported modes fail.
Archive-context mutation and expressions have separate exits.
[Aggregate field grammar](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/ConfigBodyGrammar2026.md)

The independently inspected SOLIDWORKS SP05.2 `34.5.2.0604` model
module has SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
The sketch manager serializer span `[0x4c90b140,0x4c90b2fc)`
directly calls `moFeature_c::Serialize` at `0x4c90b167`, then
stores the 16-byte `f380` at `0x4c90b246` before descending into the
pointed-to map without a separate object tag. The map serializer span
`[0x4c9080f0,0x4c909233)` owns the signed ID, its nullable reference,
then the signed and unsigned count words. The bounded sketch profile
requires the observed backlink to its own new object and both maps empty.
The header of the embedded map allocates no map entries.

The exploded view serializer span `[0x4b66d5e0,0x4b66d779)` uses
the same feature base. It reads two nullable links, a double and two
i32 values, then the inline word map. Both concrete classes use virtual
slots `0x4b8` and `0x4c0` for the feature's lightweight and resolved
prefixes. Both have an enabled `0x3f8` flag. Slot `0x3e8` is
explicitly empty for the sketch manager and selects the guarded XML
layout for the exploded view manager. The measured ordinary stream
has no XML payload on that branch. Both inherited feature profiles
restrict unsupported auxiliary objects and present optional names.
[Exact native function spans and ordered calls](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/CommonPartOwners2026.md)

## Physical controls and queue scope

The [source manifest](../measurements/2026/ConfigFieldActionsSource01.json)
pins the unchanged tracked L1 and ConcaveOwned files, both full
`Config-0` stream hashes and the cursor observations made with the
aggregate full-configuration reader.

| Control | Part field | Half-open interval | Map counter | Observed owner |
| --- | --- | --- | --- | --- |
| L1 boss | `fe80` | [24301, 24500) | 97 to 99 | Sketch class slot 97, object slot 98 and self backlink at 24490 |
| L1 boss | `f13f8` | [25159, 25354) | 108 to 110 | Exploded view class slot 108 and object slot 109 |
| ConcaveOwned | `fe80` | [22500, 22502) | 90 to 90 | Null |
| ConcaveOwned | `f13f8` | [22662, 22664) | 94 to 94 | Null |

The process independently reopens the immutable container, checks the
exact owner intervals and seeds the bounded reader with the actual map
counter and the already parsed relation and color map entries. The
second role retains the first record's entries by identity. Unused
intervening entries remain unmaterialized. The sketch body resolves
its self backlink through its own newly allocated slot. The malformed
cases cover a wrong counter, a null or genuine prior color-object
backlink, a recycled root, truncation inside the fixed field, trailing
bytes, wrong role or version, a missing virtual and unsupported
populated field and map states. An authored single-row exploded word
map exercises its concrete suffix after both native record reads.

```sh
python -I -B re/tooling/sw2026/CheckCfgOwners.py ladder
python -I -B re/tooling/sw2026/CheckCfgOwners.py concave
```

The new verifier prohibits file and external runtime access while
dispatching the bounded records. The new scoped reader awaits the
[merge-queue process cases](../../../tests/Convert/Solidworks/Configuration/CfgActionTests.py).
The observed cursor evidence above comes from the pinned reference.

## Remaining closure

The pinned full reference traces execute 141 layouts on L1, 126 on
ConcaveOwned and 141 in their union. Both exercise the same 20 action
kinds. The reader still needs handlers for `BBoxCache`, `Boolean`,
`Context`, `Direct`, `GhostCount`, `MassCaches`, `Normalize` and
`Section`. The L1 thread manager offers the next bounded Boolean control.
`moPart_c.f12d0` reaches `moCThreadRefMgr_c` at [25101, 25132)
with class slot 106, object slot 107 and the physical empty-map Boolean
word. [Exact dependency census](../measurements/2026/ConfigFieldActionsSource01.json)

Broader branch predicates, expressions, fixed and expression repeats,
directly owned nodes, packed rows and cross-owner validation remain
separate aggregate paths. The linked layout also needs the model and
part sections, annotation, presentation, view and material owners, and
real ModelHeader identity binding before complete physical `Config-0`
cursor exhaustion. Populated sketch and exploded view maps and the
write-side handlers remain outside this slice. Public configuration
admission and native writer acceptance remain open.
