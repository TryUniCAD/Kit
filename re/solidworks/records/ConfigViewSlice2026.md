# Ordinary SOLIDWORKS configuration view records

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-VIEWS` |
| Owner | PR #121 takeover team |
| Delivery | Separate main-target branch `codex/solidworks-config-view-context` |
| Preparation base | `15a4462ce69e516e36512b3185684e4778f87d30`, accepted #187 |
| Dependencies | [Member body reader](ConfigMemberFieldsSlice2026.md) and [field dispatch](ConfigFieldActionsSlice2026.md) |
| Exit | Both disclosed view groups and the authored context and refusal cases pass the guarded queue processes, followed by current revision CI and review |

## Build and archive rules

In SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`, model method
`0x4c234150` reads the ten tagged objects in `moModel_c.f9f8`.
The concrete descriptor is `moView_c`, wire schema one. Its serializer
range is `[0x4c22c9d0,0x4c22d028)`, SHA-256
`dd858d51e82d3ff05842ef4a0c0ef1d31ff3e6cf26a34f7813247abde0ccb439`.
The model module SHA-256 is
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
The serializer owns the stored name, the two embedded transforms, optional
lists and scalar words. The standard model loop also assigns the runtime
view index and localizes the name. This slice retains the original wire fields.

[Exact serializer and model loop](https://github.com/TryUniCAD/Kit/blob/a98e89e7eb1ebcb0e0ccfb5387ff2fdd76aec605/re/solidworks/records/StandardViewsConstruction2026.md#class-and-active-wire-grammar)

The shared `mgXform_c.restore` reads one byte of matrix presence,
nine doubles when that byte is nonzero, four doubles and then a flags
byte. Without an extended payload this gives 34 or 106 bytes. The
selector is the high nibble of the last byte. The shared grammar
retains original values and delegates the known extended selectors.
The bounded member role admits the compact transforms, an empty
`f380` array and absent `f398` and `f3b0` lists. Populated linked
lists and extended transforms require separate qualification.

[Exact matrix and transform read functions](https://github.com/TryUniCAD/Kit/blob/a98e89e7eb1ebcb0e0ccfb5387ff2fdd76aec605/re/solidworks/records/GeometryArchive2026.md#compact-transform-restore-path)

The shared context action consumes zero wire bytes. `Assign` sets the
named state, `Set` adds the mask, and `Clear` removes the mask. These
values govern the owning archive's subsequent fields. In `moView_c`,
`ctx87c` is assigned one before each list window and zero after it.
With `ctx3d0` active the view also sets condition bit `0x200` before
both windows and clears it before `f3c0`. Unrelated condition bits
survive both operations. The flag state accompanies the reading context.

[Context and view definition](https://github.com/TryUniCAD/Kit/blob/a98e89e7eb1ebcb0e0ccfb5387ff2fdd76aec605/re/tooling/sw2026/serial/defs/SmallCMgr.py#L408-L425)

## Native intervals and process verification

The [source manifest](../measurements/2026/ConfigViewSource01.json)
pins the two disclosed parts, complete Config-0 streams, exact-build
module identities, source rule hashes and per-record observations.
The complete aggregate reader at
`a98e89e7eb1ebcb0e0ccfb5387ff2fdd76aec605` was traced in memory
at the `f9f8` object action and the owning view's transform, string
and context field actions.

| Control | Group interval | Class slot | Object slots | Map counter | Materialized seed |
| --- | --- | --- | --- | --- | --- |
| L1 boss | [22240, 24252) | 84 | 85–94 | 84 to 95 | Relation class and object 59, 60 |
| ConcaveOwned | [20463, 22475) | 79 | 80–89 | 79 to 90 | Relation class and object 52, 53 |

Both groups declare the class once and then reuse its mapped descriptor
for nine distinct objects. Each of the twenty records executes four
`ctx87c` assignments, with no `ctx3d0` bit branch in either source.
Both transforms omit a stored matrix in the first two views. The
first transform stores nine matrix values in the remaining eight views,
and the second continues to omit the matrix. The manifest records the
actual names, framing ranges, scalar field digests, and transition offsets.

The guarded verification process independently reads the bounded
preceding relation manager, then carries those same typed objects
into the measured view counter. Slots outside the selected records
stay unmaterialized. Each bounded read uses `ReadCfgMember` with
the actual descriptor, retains inherited entries by identity, and
consumes the whole view record. Independent wire projections
check the names, transform words and fixed suffix against the
typed values.

An independently authored view reuses the L1 class and enters at its
verified end counter with `ctx3d0=1`, `ctx87c=9` and unrelated
condition bit `0x1000`. The guarded reader verifies all six ordered
state changes at byte positions 169, 177 and 193, then exits with
`ctx87c=0` and the unrelated condition still set. This is a
contrast for archive state dispatch. It supplies no native
viewport or application acceptance.

The negative cases cover incomplete and trailing fields, null or
borrowed owners, missing class slots, unsupported versions and wrong
classes, all three populated list paths, and both delegated and
unqualified transform selectors. The worker denies filesystem,
process and network access after reading its hash-bound inputs.

```sh
python -I -B re/tooling/sw2026/CheckCfgViews.py ladder
python -I -B re/tooling/sw2026/CheckCfgViews.py concave
```

[Guarded queue cases](../../../tests/Convert/Solidworks/Configuration/CfgViewTests.py)

Queue execution of this slice remains pending. The broader Config-0
graph still needs complete model sections and their remaining owners.
Annotation and user view paths, populated lists, perspective, the full
CMgr context caller and native writing retain separate acceptance.

[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
