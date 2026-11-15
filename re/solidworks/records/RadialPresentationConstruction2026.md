# Radial presentation construction in SOLIDWORKS 2026

**Status: static construction rules only. No circle or arc writer or native acceptance is established.**

This record closes the ordinary radial constructor's prefix assignment and a
single mode flag. It extends the
[curve construction ledger](CurvedSketchConstruction2026.md), without treating
constructor seeds as a complete saved display state.

## Identity and method

The model module is `sldmodu.dll`, SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`,
preferred image base `0x4b140000`. The resource module is `sldresu.dll`, SHA-256
`531cf5d1c913f60f707652f0ecae600313d0970f7e649dcadec64983c484e111`.
These are the pinned 2026 SP05.2 images, not address translations from 2025.

The existing private Ghidra 12.1.3 model database was opened with `-noanalysis`
and `-readOnly`. Targeted decompilation was checked against the actual
instructions, PE vtable entries and unwind extents. Leaf extents below stop
after the explicit return, before alignment bytes. Proprietary images,
databases and listings remain outside repository checkouts.

REA 6.7.0 `inspect_pe_resources` supplied the resource inventory as Evidence
`ev_7ba15aa4e0caa4fa740e4ce8f23a313101fe8cf32a87cec2780d85ee9a3c363e`.
Its complete inventory examined 4,738 directory entries and 2,363 resources.
REA did not decode the string payload. An independent bounded `RT_STRING`
decoder consumed its selected 1,788-byte payload exactly and verified its
REA-recorded SHA-256. Static resource ownership does not establish runtime
language selection or a successful native load.

## Prefix vocabulary and final constructor assignment

The selected resource is type `6`, block `674`, language `1033`, payload RVA
`0x242488`, file offset `2351240`, SHA-256
`c09c11dae78006df472961932633342457ab1c75a219912b9564fd84d1a85d3f`.
Each of its sixteen entries uses a UTF-16LE code-unit count followed by text.
The two format tokens used here are:

| String ID | Entry index | Count-prefix offset within payload | Code units | Format vocabulary |
| --------- | ----------- | ---------------------------------- | ---------- | ----------------- |
| `0x2a12`  | 2           | 512                                | 10         | `<MOD-DIAM>`      |
| `0x2a13`  | 3           | 534                                | 1          | `R`               |

These are minimal format vocabulary, not bytes or values captured from a model.
The diameter token is the native markup string, not a substituted Unicode
diameter glyph and not the literal letter `M`.

The radial constructor `0x4c8bfc10` initializes runtime `+0x1058` to one at
`0x4c8bfcfa`. After its position update, call `0x4c8bfdfd` invokes prefix
initializer `0x4c8cc1d0`. That helper dispatches radial virtual `+0xd08` at
`0x4c8cc1eb`, bound by radial vtable `0x4d255be0` to `0x4c8d2020`.
The latter delegates to handle `isDiametric`; the ordinary circle dimension's
virtual `+0x268` is `0x4c42a7f0`, whose explicit predicate is `f80 == 0x0f`.

| Ordinary dimension mode                                     | Helper branch                        | Computed prefix |
| ----------------------------------------------------------- | ------------------------------------ | --------------- |
| Radius, `sgCircleDim.f80 == 3`                              | `0x4c8cc267` selects string `0x2a13` | `R`             |
| Diameter, `sgCircleDim.f80 == 0x0f`, runtime `+0x1058 != 0` | `0x4c8cc1fe` selects string `0x2a12` | `<MOD-DIAM>`    |

The helper's special `S` prefix requires handle virtual `+0x4b8` to return
`0x1d`. The actual completed `moSkDimHandleValG1_c` constructor installs
vtable `0x4d242c18` at `0x4c83d520`; its `+0x4b8` slot is `0x4c844ab0`.
That method resolves the dimension through actual `+0x730`, `0x4c8460f0`,
then invokes dimension virtual `+0x338`. Circle vtable `0x4cf79588` binds
`+0x338` to the explicit zero-return leaf `0x4b27cbe0`.
Thus this special prefix is excluded by the ordinary circle's real dispatch,
not by assuming that every handle has the base class's table.

At `0x4c8cc2c0`, the helper calls `setPrefixText(prefix, 0)`.
The setter assigns the primary runtime `+0x7f8` string at `0x4c8978ec`.
That member is the current shared display schema's `f7f8` CString field.
When the prefix changes, it clears runtime `+0xad8` and cleans display data.
It also computes runtime `+0xb5c` bit `0x80` from whether the prefix contains
`/`; that bit is clear for both tokens. The caller's zero third argument
skips the setter's optional secondary-text dispatch.

The subsequent constructor call `setUseNumInstFlag(1)` at `0x4c8bfe0a`
only sets runtime `+0xb60` bit `0x200`, the current wire field `fb60`.
The remaining constructor stores and flag OR operations do not overwrite
`f7f8`. The two prefixes above therefore describe the completed constructor's
primary prefix, rather than its earlier empty-string seed.

Runtime `+0x1058` and the slash bit at `+0xb5c` are not separate fields in the
current radial wire schema. Their operational roles do not authorize adding
new archive bytes or replacing the existing serializer order.

## Forced radial mode flag

In the reached ordinary engine-update branch, instructions
`0x4c8dc91c`–`0x4c8dc92d` invoke radial virtual `+0xd10` with the actual
`isDiametric` result and force argument one. Its target is `0x4c8d4bc0`.
For ordinary runtime `+0xf84 == 0`, this function computes:

| Input mode | `ffd8` operation | Native call and store                           |
| ---------- | ---------------- | ----------------------------------------------- |
| Radius     | Set bit `0x10`   | Handle wrapper `0x4c84c910`; store `0x4c8d4d1d` |
| Diameter   | Clear bit `0x10` | Handle wrapper `0x4c84b650`; store `0x4c8d4c9a` |

The same operations occur in the no-prefix branch at
`0x4c8d4c1d`/`0x4c8d4c2e`. The force argument prevents the early
same-mode return at `0x4c8d4bf8`.

The wrappers resolve the actual dimension and call its `+0x270/+0x278`
methods, bound to `0x4c431170/0x4c42f850`. Those methods change only the
opposite mode: diameter-to-radius multiplies the parameter by `0.5`, while
radius-to-diameter multiplies it by `2.0`, then changes `f80` and invokes the
parameter setter. The multipliers are literal binary64 constants at
`0x4cd9a3c0/0x4cd9e318`. Passing the already queried mode leaves the circle's
type and value unchanged at this boundary. A forced display update is not an
extra radius-to-diameter conversion.

Only this flag bit is closed here. The complete `ffd8` value still requires
the other ordered mutations and their native acceptance. In particular,
neither constructor `0x80086` nor its final two OR operations prove that the
whole persisted flag word is universal.

## Function fingerprints

All model extents below are half-open and use the pinned model-module hash.

| Function or boundary                                     | Extent                    | SHA-256                                                            |
| -------------------------------------------------------- | ------------------------- | ------------------------------------------------------------------ |
| Radial constructor                                       | `[0x4c8bfc10,0x4c8bfe5a)` | `bc2bbf09a91cdcb5c68b134df358fb3c8b7e61c83fecf2b1096249c1012e90ba` |
| Prefix initializer                                       | `[0x4c8cc1d0,0x4c8cc2d7)` | `45683ad6f31b269da94f3c2ac9952d92de71eaccfe0790f27fa8194e8294a0e5` |
| Prefix setter                                            | `[0x4c8978b0,0x4c897973)` | `fb8b8cd6c17a8b317eaa2974fbac937e24c8d85984ee0ab359200b97f9896f8f` |
| Swift-type resolver                                      | `[0x4c844ab0,0x4c844ada)` | `116ca9705fa5594d0963c978b22f1ae61f0b6bd26b009c31cbbfcd20d742b676` |
| Actual sketch-dimension resolver, three unwind fragments | `[0x4c8460f0,0x4c8461ae)` | `babaf99b1ea9f17d8ee87ed1dbc46c4feb6f4edcc777bde0d7435cc9482eeea2` |
| Diameter predicate leaf                                  | `[0x4c42a7f0,0x4c42a7fd)` | `a8f4c8d26dd1d03fcf869d9d7c75242f0291df42e4b37ffea27bd60214575371` |
| Zero-return leaf                                         | `[0x4b27cbe0,0x4b27cbe3)` | `4bc724f3b1d0caf4fe369c18cba3102e6c4ea057f63fe1587e3973134a7f755e` |
| Forced mode setter                                       | `[0x4c8d4bc0,0x4c8d50c3)` | `8cbc862add2f8a410551ab11076a21732d0961151a2e96d9ae8ddc5bbc0c7774` |
| Radius-mode wrapper                                      | `[0x4c84c910,0x4c84c947)` | `d97bfb3612152243d1c5bf456bb3729a5b306abfd372788844f05bedb8de03f6` |
| Diameter-mode wrapper                                    | `[0x4c84b650,0x4c84b687)` | `bd693d0168bb01d9bb9bb499a822652fb480853c9fd4a0a7b50b5d598c356fe3` |
| Diameter-to-radius operation                             | `[0x4c431170,0x4c4311e1)` | `af90bf6e617a7c5ffd72c368f3170179db40afcb0d5300093a05488a189ddeb3` |
| Radius-to-diameter operation                             | `[0x4c42f850,0x4c42f8c1)` | `8905cb0bd33e14f269b2de1d4a440ab2bd113b6320b6d94bba4ba9893e0766e3` |
| Instance-count flag leaf                                 | `[0x4c898ce0,0x4c898d01)` | `d1c0e21da87d20f5abf87dc74968238445add715ad09feb829b9bc8cb444b11d` |

## Remaining obligations

The full-circle witness assignment remains proved at its guarded engine-update
boundary. The rest of that method has no later direct reference to its two
witness members, but calls further helpers and virtual methods. That bounded
negative observation does not prove their final saved values.

Final tolerance ownership, remaining radial flags and placement fields, later
update and restore behavior, and full curve source-lock/held-out acceptance
remain open. No oracle launch, attachment, document mutation, local test,
held-out stream inspection or writer implementation occurred for this finding.
