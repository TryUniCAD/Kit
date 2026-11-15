# SOLIDWORKS 2026 style and unit construction

Status: **fresh standard-1 detail graph and unit constructors implemented;
remote process checks pending; target acceptance unproven**. The graph contains
typed dimension, annotation, table, label, helper and Swift records. Unsupported
standards fail closed. This research component constructs candidates for the
parent model builder; it does not claim a usable native document. No source
save, captured row, recorded field program or runtime CAD input is used.

## Binary identity and static evidence

The 2026 `sldmfcu.dll` has SHA-256
`af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`.
Its `moDetailDefs_c` constructor is `0x3c7d1270`.
The [binary manifest](../v2026/Manifest2026.json) binds the original model and
format DLLs. Static decompilation used private copies of existing projects,
opened read-only. No shared analysis database was changed.

The constructor and native callees establish these rules independently of a
part's feature count or saved values:

| Record or rule             | Native owner and address                                                         | Construction evidence                                                                                                                                  |
| -------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| detail root                | `sldmfcu.dll` `0x3c7d1270`                                                       | constructs separate dimension, annotation, table, label and helper graphs; then applies standard defaults                                              |
| standard rules             | `sldmfcu.dll` `0x3c7da220`                                                       | dispatches standard-specific child rules; sets root spacing and font height                                                                            |
| root `f138` and Swift mode | `sldmfcu.dll` instructions `0x3c7d183d`–`0x3c7d1852`                             | `int(standard != 0)` is stored at `f138` and passed in `edx` to `0x3c7db840`, which writes embedded Swift `f3dc`; the decompiler omitted that argument |
| character format           | `sldmfcu.dll` `0x3c7bf430`, `0x3c7bf510`, `0x3c7bf5f0`, initializer `0x3c7c0710` | explicit face, system height or point-height mode, spacing/width settings, flags and weight; constructor literals are distinct from authored overrides |
| line weight                | `sldmfcu.dll` `0x3c84a8f0`                                                       | category argument, width `-1` meaning category-selected width; the sentinel is not zero                                                                |
| print widths               | `sldmfcu.dll` `0x3c84adb0`, preference overlay `0x3c84b060`                      | eight widths; caller supplies authored widths instead of reading registry preferences                                                                  |
| dimension graph            | `sldmfcu.dll` `0x3c7dedb0`, default rules `0x3c7e1200` and `0x3c7da4e0`          | constructs ten typed dimension defaults, applies common and subtype-specific standard rules                                                            |
| base dimension             | `sldmfcu.dll` `0x3c7dea20`, standard rule `0x3c7e0d60`                           | owns two fresh unit records, two line-font configurations, text format, layer sentinel and dimension flags                                             |
| annotation helper          | `sldmfcu.dll` `0x3c7d0fe0`                                                       | constructs its own default character format and explicit scalar seeds                                                                                  |
| unit base                  | `sldmfcu.dll` `0x3c9081d0`, serialization `0x3c90d170`                           | initialized field order and typed constructor parameters; no schema-wide zero fill                                                                     |
| unit table                 | `sldmfcu.dll` `0x3c8ebd10`, default factory `0x3c8ec680`                         | constructor argument selects whether to create sixteen native unit types; custom tables count their actual constructed rows                            |

## Resource vocabulary

The constructor references English language `0x409` resources in 2026
`sldresu.dll`, size 4,461,656 bytes, SHA-256
`531cf5d1c913f60f707652f0ecae600313d0970f7e649dcadec64983c484e111`.
The following original PE file locations were independently decoded through the
RT_STRING length-prefixed UTF-16 entries:

| Resource id | File offset | Vocabulary     |
| ----------- | ----------- | -------------- |
| `0x3013`    | `0x2c03b0`  | Century Gothic |
| `0x4aa0`    | `0x3fc1b2`  | Description    |
| `0x36f0`    | `0x1e3e12`  | High Priority  |
| `0x36f1`    | `0x1e3e2e`  | Low Priority   |
| `0x4a73`    | `0x3b0e18`  | Complete       |
| `0x4a8d`    | `0x3b1766`  | Reminder       |

These are constructor-referenced locale vocabulary, not values taken from a
saved document. Explicit authored font and label overrides remain supported.
The writer will not load the resource DLL at runtime.

## Unit ownership

The model constructor initializes `f9b8` and `f9c0` to null. The 2026 owner
methods in `sldmodu.dll` establish separate user and analysis tables:

| Method                  | Address                     | Rule                                                                                                           |
| ----------------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `getAnalysisUnitsTab`   | `0x4c01d380`                | mode 1 returns user `f9b8`; mode 2 prefers analysis `f9c0` and falls back to user; other modes return analysis |
| `resetUserUnitsTab`     | `0x4c031e20`                | replaces `f9b8`, increments the new table's use count and decrements the old table's use count                 |
| `resetAnalysisUnitsTab` | `0x4c0318c0`                | the same ownership rule for `f9c0`                                                                             |
| default length / angle  | `0x4c01f680` / `0x4c01f210` | look up the requested runtime class through the model's user-table virtual slot `0x1008`                       |
| default density         | `0x4c01f240`                | adds a missing density row; reattaches its derived length-unit copy when needed                                |
| default unit system     | `0x4c01fdd0`                | adds a missing `moUnitSysUnits_c(3, 2)` row                                                                    |

The old-version loader's creation of a default table below version `0xf98` is
not evidence of a 2026 default. Both primary model vtables, `0x4d0c70e0` and
part `0x4d1252d8`, resolve slot `0x1008` to `0x4b69e2e0`, whose complete body
returns `[this + 0x9b8]`. Default length and angle therefore use the document/user
table, independently of the analysis-mode helper.

### Unit names and factors

`sldappu.dll!CAmApp::initUnitAbbreviations` at `0x4580f7a0` constructs named
`unitStrEntry` records with explicit conversion factors and enum ids. It calls
the length-map setter at `0x458118e1`. The static map establishes these numeric
vocabulary rules without relying on a public-API analogy or a saved control:

| Kind        | Semantic unit → native enum                          | Factor from system units                                     |
| ----------- | ---------------------------------------------------- | ------------------------------------------------------------ |
| length      | mm → 0; cm → 1; m → 2                                | 1000; 100; 1                                                 |
| length      | in → 3; ft → 4                                       | 39.37007874015748; 3.280839895013123                         |
| length      | angstrom → 6; nm → 7; um → 8                         | 1e10; 1e9; 1e6                                               |
| length      | mil → 9; microinch → 10                              | 39370.078740157485; 39370078.740157485                       |
| angle       | degree → 0; arcminute → 1; arcsecond → 2; radian → 3 | 57.295779513082195; 3437.7467707849314; 206264.8062470959; 1 |
| unit system | CGS → 0; MKS → 1; IPS → 2; MMGS → 4                  | literal system names, not a scale factor                     |

Length code 5 shares the inch conversion factor but its composite display
semantics remain outside the semantic-name API. Native constructor system code
3 is not one of the four named map entries; it is not labelled MKS or MMGS.
The primitive `unit_record` exposes only recovered constructor/map code domains.
`unit_table_profile` builds sixteen fresh records in the native factory's class
order while taking explicit length, angle, system and precision inputs. The
profile's other unit types use their actual native constructor choices; no
vendor save is used to supply them.

## Construction interface

`builders.Styles.detail_definitions(*, standard, font_name, line_style_name,
language_id, print_widths_m, exclusion_names, task_labels,
cutlist_expressions)` returns a fresh dictionary for the model root's embedded
`fae0`. `standard` must be integer 1. Fonts, line-style names, language id,
eight print widths, exclusion names, five task-column labels and three cut-list
id expressions are explicit authored semantic inputs. They are not captured
preferences or metadata from another document. The constructor does not read
the registry, resource DLLs, corpus or a source model.

`builders.Units.unit_record(*, kind, unit_code, decimal_places)` returns a
fresh `Core.Obj`. `units_table(*, definitions)` creates a counted table from
semantic definitions with exactly those three keys. `unit_table_profile(*,
length_unit, angle_unit, unit_system, decimal_places)` creates the sixteen
native factory types with explicit named length, angle, system and precision
choices. This is a Kit-authored profile built from native class rules, not a
claim to reproduce a user's application preferences. Explicit rows can form a
different table; the parent must choose a table adequate for the model's needs.

Embedded schema records are dictionaries recursively. Explicit object slots,
such as a unit-table row, are `Core.Obj` instances. There is no byte template,
field-program replay, opaque payload or missing-key zero fallback.

## Field classification

`Input` means an explicit neutral-document or authored setting. `Derived` means
the stated formula or composition. `Seed` means a literal assignment or branch
in the identified 2026 constructor, not invariance among related input files.
`Compatibility seed` is weaker: the current reader supplies it for a supported
older record. None of these classifications establishes vendor acceptance.
Offsets name memory fields as used by the existing typed wire schemas.

### Detail root

The following root groups all belong to `sldmfcu.dll!moDetailDefs_c`, constructor
`0x3c7d1270`, standard dispatch `0x3c7da220`. Repeated scalar assignments are
explicit constructor statements; the two grid loops cover only native-owned
grid storage, not arbitrary missing schema fields.

| Fields                                                                                                                                                                                                                                                                                       | Classification and computation                                                                                         | Evidence                                                                                                                             |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `f10`                                                                                                                                                                                                                                                                                        | Input: supported standard 1                                                                                            | constructor stores standard; native dispatch accepts 0–6, only branch 1 implemented                                                  |
| `f90.f08`, `fa0.f08`, `fa8.f08`, all descendant face names                                                                                                                                                                                                                                   | Input: authored font name                                                                                              | constructor resource `0x3013`; explicit override substitutes vocabulary only                                                         |
| `fb0.f08..f24` step 4                                                                                                                                                                                                                                                                        | Input: eight authored print widths in metres                                                                           | print-width ctor `0x3c84adb0`, registry overlay `0x3c84b060` deliberately not called                                                 |
| `n58`, `f58`                                                                                                                                                                                                                                                                                 | Derived: count and rows from authored exclusion names                                                                  | native string array; `iInitExclusionList` `0x3c7db220` fills preferences, caller supplies names instead                              |
| `fb8.n`, `fb8.items`                                                                                                                                                                                                                                                                         | Derived: five task-label strings supplied by caller                                                                    | constructor loads resource ids `4aa0,36f0,36f1,4a73,4a8d` in that order                                                              |
| `f200`, `f208`, `f210`                                                                                                                                                                                                                                                                       | Input: cut-list id expressions                                                                                         | getters `0x3c7d93f0` keys `0x81,0x82,0x83`; constructor helpers `0x3c7d8bb0`, `0x3c7d84f0`, `0x3c7d8380` build localized expressions |
| `f08`, `f28`, `f34`, `f90.f10`                                                                                                                                                                                                                                                               | Seed: standard-1 spacing `0.002`, mark size `0.0025`, centreline mode 1, text height `0.0035`                          | dispatch `0x3c7da220`; folded setters verified by actual target offsets                                                              |
| `f138`                                                                                                                                                                                                                                                                                       | Derived: `int(standard != 0)`                                                                                          | raw instructions `0x3c7d183d..0x3c7d1852`                                                                                            |
| `f20`                                                                                                                                                                                                                                                                                        | Derived bit mask: centreline `0x100000`, graphic bodies `0x40000`, table settings `0x4000`; halo enabled clears `0x80` | setters `0x3c7db8c0`, `0x3c7dbb30`, `0x3c7dc490`, `0x3c7dc300`                                                                       |
| `fec,ff0,ff4,f110,f114,f118`                                                                                                                                                                                                                                                                 | Seed: native precision lists `2,3,4` for length and angle                                                              | constructor literal assignments after child initialization                                                                           |
| `ff8,f100,f108,f120,f128,f130,f140,f148`                                                                                                                                                                                                                                                     | Seed: native tolerance magnitudes, stored as exact constructor double values                                           | constructor assignments at the same offsets; angle values are not recomputed from a rounded degrees constant                         |
| `f228..f284`, `f288..f2e4` step 4                                                                                                                                                                                                                                                            | Seed: zero values in two native 3×8 integer grids                                                                      | constructor runs two 3-iteration loops, each clears four qwords per row                                                              |
| `f13b0,f1f18,f2410,f2750`                                                                                                                                                                                                                                                                    | Derived: fresh dimension, annotation, table and label graphs                                                           | root owns embedded typed records and invokes their standard mutations                                                                |
| `f2e8,f4d8,f730,f9a0,fb88,fcd8,fde0,ff68`                                                                                                                                                                                                                                                    | Derived: fresh helper graphs, detailed below                                                                           | root constructor explicitly constructs each child                                                                                    |
| `f13a0,f2bd8,f2be8,f1c8`                                                                                                                                                                                                                                                                     | Seed: empty constructor strings                                                                                        | constructor CString initialization                                                                                                   |
| `f1c0,f1d0,f1d8,f1f0`                                                                                                                                                                                                                                                                        | Seed: literal vocabulary `Plate,`, `x`, `x`, `Sheet`                                                                   | constructor wide-string literals; no saved file consulted                                                                            |
| `f30,f3c,f14,f18,f1c,f1388,fe8,f150,f154,f158,f15c,f160,f164,f168,f16c,f170,f174,f40,f138c,f1390,f1394,f1398,f44,f48,fe0,fe2,f50,f4c,f178,f17c,f180,f184,f188,f18c,f190,f194,f198,f19c,f1a0,f1a4,f1a8,f1ac,f1b0,f1b4,f1b8,f1bc,f1e0,f1e4,f1e8,f1f8,f1fc,f218,f21c,f220,f224,f54,f80,f88,f98` | Seed: explicit native scalar assignments, split into wire-width fields where a native qword initializes two integers   | root ctor `0x3c7d1270`; values written individually in `Styles.py`                                                                   |
| `f2bc0,f2bc8,f2bd0,f2be0,f2bf0,f2bf4,f2bf8,f2bfc,f2c00,f2c04,f2c08,f2c0c,f2c10,f2c18,f2c20,f2c28,f2c30,f2c38,f2c40,f2c44,f2c48,f2c4c,f2c50,f2c54,f2c58,f2c5c,f2c64,f2c68,f2c6c`                                                                                                              | Seed: explicit native scalar assignments                                                                               | root constructor; long doubles and split qwords follow actual field widths, not byte padding                                         |

### Primitive and unit records

| Fields                                                 | Classification and rule                                                                                                                                                            | Native owner                                                                                                  |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| character `f08`                                        | Input: face name                                                                                                                                                                   | `sldmfcu.dll` `0x3c7c0710`                                                                                    |
| character `f10,f18`                                    | Derived mode: positive system height with zero points, or height `-1` with authored/native point height                                                                            | explicit constructors `0x3c7bf430`, `0x3c7bf510`                                                              |
| character `f20,f28,f30,f38,f40,f48,f50,f58`            | Seed: escapement 0, explicit/default-helper line spacing, flags 0, width 1, oblique 0, line width 0, character spacing 1, weight 400; primitive API allows authored spacing/weight | initializer `0x3c7c0710`; helper default ctor `0x3c7bf5f0` supplies line spacing `0.001`                      |
| line weight `f06,f00`                                  | Input/seed: category 0–7 and width, or native width sentinel `-1`                                                                                                                  | `0x3c84a8f0`                                                                                                  |
| line font `f08,f10,f18`                                | Input name; fresh category-0 width record; native end cap 0                                                                                                                        | `uiLFConfig_c` `0x3c848680`                                                                                   |
| unit `f0c`                                             | Input: precision integer 0–16                                                                                                                                                      | precision setter `0x3c755c30` clamps to maximum 16; builder rejects out-of-domain input                       |
| unit `f08,f10,f18,f20,f24,f28,f30,f6c,f70,f74,f7c,f88` | Seed: shared native minimal-constructor formatting (`0,1,.01,10,1,1,pi/4,0,1,1,0,0`)                                                                                               | base initializer `0x3c9081d0`; minimal length/angle ctors `0x3c9066f0`, `0x3c905b50`                          |
| unit `fb0` where present                               | Input: recovered class-specific enum domain; named profile maps above                                                                                                              | `sldappu.dll` `0x4580f7a0`; force/power/energy/time ctors `0x3c9063b0`,`0x3c906c90`,`0x3c9062e0`,`0x3c907ca0` |
| length `fb8`                                           | Seed: null child                                                                                                                                                                   | length ctor `0x3c9066f0`                                                                                      |
| density `fc0,fc4,fc8,fcc,has_fb8,fb8`                  | Seed: `3,1,3,1,0,null`; the separately cloned nonserialized length child is not emitted as this optional object                                                                    | density ctor `0x3c905f60`, length attachment `0x3c91b870`                                                     |
| table `n,items`                                        | Derived: actual constructed object count and rows; all sixteen profile nodes are distinct                                                                                          | default factory `0x3c8ec680`; table ctor `0x3c8ebd10` supports an explicitly empty initial table              |

### Dimensions, annotations, tables and labels

| Record and field group                                                      | Classification and native rule                                                                                                                                  | `sldmfcu.dll` evidence                                                                                                                                                                |
| --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| dimension root `f08..f58` doubles, `f60..fd8` scalars                       | Seed: native constructor assignments followed by standard-1 arrow/spacing, break distance, bent-leader and precision rules                                      | ctor `0x3c7dedb0`, rules `0x3c7e1200`, root dispatch `0x3c7da4e0`                                                                                                                     |
| base dimension `f08..fc0`, `fe0`                                            | Seed: explicit formatting flags, precision fields and layer `-1`; standard 1 clears broken/leader override bits and selects standard-specific places            | ctor `0x3c7dea20`, base rules `0x3c7e0d60`                                                                                                                                            |
| base dimension `fd0,fd8,fe8,ff0,ff8`                                        | Derived: two authored-name line fonts, authored-face text format and fresh metre/degree records with native precision 2                                         | same ctor; embedded length/angle constructors, not global preference copies                                                                                                           |
| derived dimensions `f100..f128` where present                               | Seed: type-specific explicit fields and standard mutations for linear, angle, arc length, radial, hole, ordinate, angular ordinate, chamfer and diameter        | ctors `0x3c7df200`,`0x3c7de9c0`,`0x3c7de9f0`,`0x3c7df2e0`,`0x3c7df1c0`,`0x3c7df290`,`0x3c7de970`,`0x3c7decd0`,`0x3c7ded70`; rules `0x3c7e0b10`,`0x3c7e2890`,`0x3c7e1170`,`0x3c7e0ae0` |
| annotation root scalars and ten embedded records                            | Seed/derived: native standard-1 arrow and bend rules; independent typed children                                                                                | ctor `0x3c7a3100`, rules `0x3c7a4900` and `0x3c7da210`                                                                                                                                |
| base annotation `f08,f10,f18,f20,f24,f28,f34,f40,f44`                       | Seed: standard 1, text/leader scalar initialization, layer `-1`; typed line widths `f2c,f38`; authored-face `f50` height `.0035`                                | ctor `0x3c7a3410`, rules `0x3c7a4bf0`                                                                                                                                                 |
| base annotation `f1c`                                                       | Derived: right alignment 2 when `(language_id & 0x3ff) == 0xd`, otherwise 0                                                                                     | native `GetUserDefaultLangID` branch replaced with explicit authored language input                                                                                                   |
| annotation subtype extra fields                                             | Seed: cloud arc size; weld secondary font; finish parameters; bend-note flags; GTol flags; datum flags; balloon layout; view-location fields; note fit settings | ctors `0x3c7a3670`,`0x3c7a3770`,`0x3c7a36b0`,`0x3c7a3540`,`0x3c7a35d0`,`0x3c7a3590`,`0x3c7a32f0`,`0x3c7a3700`,`0x3c7a3610`; rules `0x3c7a4ac0`,`0x3c7a4eb0`,`0x3c7a5070`              |
| table root `f08,f328,f330,f338` and nine children                           | Seed/derived: standard 1, authored-face text `.0035`, two native clearances, fresh child styles                                                                 | ctor `0x3c8d3880`, rules `0x3c8d4d40`                                                                                                                                                 |
| base table `f08,f0c,f28,f2c,f38,f10,f18,f20`                                | Seed/derived: flags 0, layer `-1`, standard 1, authored-face text `.0035`, native category-width children                                                       | ctor `0x3c8d3640`, rules `0x3c8d4ad0`                                                                                                                                                 |
| table subtype extra fields                                                  | Seed: explicit revision/BOM/hole/weld/bend/punch/family initialization, inherited base standard/font rules                                                      | ctors `0x3c8d3830`,`0x3c8d35b0`,`0x3c8d3740`,`0x3c8d3b80`,`0x3c8d3600`,`0x3c8d37c0`,`0x3c7d1b20`; folded defaults `0x3c8d4a00`                                                        |
| label root `f08,f0c,f458` and five children                                 | Seed/derived: native label selectors, authored-face text `.0035`, fresh typed label records                                                                     | ctor `0x3c847780`, standard dispatch `0x3c7da600`                                                                                                                                     |
| base label `f08..f58,f88,f90` and `f98..fc0` formats                        | Seed/derived: native label syntax, scale/name/inline modes, line widths and strings; six independent authored-face text records                                 | ctor `0x3c86c580`; base rules `0x3c86e490`; derived out-of-box rules `0x3c86fe60`,`0x3c86ff90`,`0x3c86fda0`,`0x3c86ff00`                                                              |
| label `f5c`                                                                 | Seed: clockwise bit `0x4`                                                                                                                                       | native setter `0x3c86fd20`, called with 1 by base ctor                                                                                                                                |
| detail `fc8,fcc`; section `fc8..ff0`; auxiliary `fc8`; ortho/misc `fc8,fcc` | Seed: subtype flags, section arrow geometry and label width category 2                                                                                          | ctors `0x3c86c190`,`0x3c86cb00`,`0x3c86c0d0`,`0x3c86ca10`,`0x3c86c970`; standard rules `0x3c847a90`,`0x3c86e7b0`,`0x3c86e6f0`                                                         |

### Helpers and Swift

| Record and field group                  | Classification and rule                                                                                                                                    | Native evidence                                                                                                                       |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| annotation helper all serialized fields | Seed/derived: native flag/scalar initialization and fresh authored-face default format                                                                     | `sldmfcu.dll` ctor `0x3c7d0fe0`                                                                                                       |
| surface finish all serialized fields    | Seed/derived: empty native strings, explicit type flags, native `pi/4` angle and two child formats                                                         | ctor `0x3c7d2710`                                                                                                                     |
| note all serialized fields              | Seed/derived: native text/leader/border flags, empty counted property table and child formats                                                              | ctor `0x3c7d24b0`                                                                                                                     |
| weld all serialized fields              | Seed/derived: two-sided native string/flag arrays, three fresh formats and two finish helpers                                                              | ctor `0x3c7d2850`                                                                                                                     |
| GTol frame all serialized fields        | Seed/derived: two fresh frames, empty text arrays, null tolerance nodes, `f148=0` disables datum payloads, zero indicator count                            | frame ctor `0x3c7d1cc0`; helper allocation `0x3c7d9800`                                                                               |
| GTol helper fields other than `f80`     | Seed/derived: native fields, two frame rows and child formats                                                                                              | helper ctor `0x3c7d1b50`, copy `0x3c7d76b0`                                                                                           |
| GTol helper `f80`                       | Compatibility seed 0, matching the 2026 reader's explicit pre-`0x3751` fallback; not a constructor-derived constant and its application role is unresolved | serializer/loader `0x3c85ce50`; both owner transfer methods only copy it (`0x3c7db630`,`0x3c7dc8f0`)                                  |
| centre mark all serialized fields       | Seed/derived: explicit native flags/geometry scalars and annotation helper                                                                                 | ctor `0x3c7d1080`                                                                                                                     |
| datum feature all serialized fields     | Seed/derived: native strings and flags, fresh annotation helper                                                                                            | ctor `0x3c7d1120`                                                                                                                     |
| datum target all serialized fields      | Seed/derived: native flags, `0.03` sizes, unused direction initialized to `(0,0,0)`, fresh annotation helper                                               | ctor `0x3c7d1180`; `sldmgu.dll` unit-vector ctor `0x31f19380` calls vector storage initializer `0x31dd3a00` with three zero registers |
| Swift serialized double fields          | Seed: metric tolerance branch `setDefaultTolerances(this,1)` with constructor selector `f08=0`; positive/negative pairs computed from the same magnitude   | ctor `0x3c83c4a0`, defaults wrapper `0x3c83f670`, tolerance rules `0x3c83fcc0`                                                        |
| Swift precision integer fields          | Derived: native `max(2, minimum)` where the metric minima are 1 or 2, therefore 2                                                                          | precision rules `0x3c83fa60`; maximum helper `0x3c798f40`                                                                             |
| Swift remaining integer flags           | Seed: explicit constructor assignments and flag initializer; the three wire occurrences of `f220` all read the same initialized precision field            | flag rules `0x3c83f8d0`; serializer `0x3c83c760`                                                                                      |
| Swift `f3dc`                            | Derived: `int(standard != 0)` in the owning root; not serialized by the current schema                                                                     | helper `0x3c7db840`, raw caller `0x3c7d184b`                                                                                          |

## Verification and remaining acceptance

Static AST parsing, formatting, type checking and repository naming checks are
the only local checks. No local tests, reproductions, collection, builder imports
or target application operations have run. The process-boundary checks create
independent child Python processes, block filesystem access after loading the
codecs, build from authored JSON, encode/decode typed records and require exact
wire round trips. They also vary text, language, exclusion counts and unit-table
shape. They are scheduled through the existing remote workflow-quality native
file-reading/writing step; no separate workflow or donor access is introduced.

Remaining acceptance includes vendor load/rebuild/edit checks in the assembled
document, the unresolved semantic role and held-out acceptance of the GTol `f80`
compatibility seed, non-1 standard branches, optional populated GTol/datums and
full authored dimension/annotation preference coverage. Helper constructors
describe unused style records, not user-created annotations or feature support.
Native constructor seeds are not inferred from ladder invariance. The unit
profile and style graph are not a production-ready writer by themselves.

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
state: “There are two acceptable stopping conditions. The first is success under
every criterion on this page. The second is the end of the available context.
Missing grammar is the work. It is not a blocker.” This component does not
change those conditions or complete the parent writer goal.
