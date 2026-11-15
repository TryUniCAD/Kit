# SOLIDWORKS 2026 header construction fields

Status: **partial construction evidence; no fresh header accepted in SOLIDWORKS**.
The source codec passed byte identity on the eight related ladder inputs.
Those inputs do not prove general constants or a neutral-document builder.

## Binary identity

All addresses in the following table belong to 2026 `sldarchiveu.dll`, SHA-256
`5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48`.
`moHeader_c` constructor begins at `0x31a02540`.
Constructor seeds below come from instructions, not values copied from a saved part.
They are not independently accepted output defaults.

| Field                        | Role and construction rule                                                                                   | Constructor seed                                 | Binary evidence                                                       |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------ | --------------------------------------------------------------------- |
| `f08`                        | derived next persistent id; highest id is `f08 - 1`; allocation increments and skips reserved ids            | 0                                                | `0x31a05230`, `0x31a052d0`                                            |
| `f10`                        | input user-name string array; indices must agree with stamps                                                 | null                                             | `0x31a049d0`, `0x31a03120`                                            |
| `f18`                        | input company-name string array                                                                              | null                                             | `0x31a030b0`                                                          |
| `f20`                        | derived revision-log graph                                                                                   | null                                             | `0x31a04da0`, `0x31a05420`                                            |
| `f28`                        | input linked-attachment names                                                                                | null                                             | `0x31a052c0`                                                          |
| `f30`                        | derived external-object reference list                                                                       | null                                             | `0x31a04d10`, `0x31a05200`                                            |
| `f38`                        | derived self external-object reference                                                                       | null                                             | `0x319f89d0`                                                          |
| `f40`                        | derived mutable update-stamp counter                                                                         | 101                                              | constructor `0x31a02580`; getter `0x319f9810`; decrement `0x31a04f20` |
| `f44`                        | derived body-stamp counter; increments on allocation                                                         | 101                                              | constructor `0x31a02587`; getter `0x319f8a10`; increment `0x31a05340` |
| `f48`                        | volatile update timestamp                                                                                    | local `su_CTime(1990,1,1,0,0,0,-1)` construction | constructor call `0x31a025b4`; getter `0x319f8a60`                    |
| `f50`                        | volatile timestamp with save-time normalization                                                              | `ut_getUnsetTime()`                              | constructor `0x31a025ba`; serializer `0x31a034f0`                     |
| `f58`                        | derived lock state; lock/unlock write 1/0; loader clears saved state                                         | 0                                                | `0x31a058b0`, `0x31a062b0`                                            |
| `f60`                        | derived break-id allocation counter                                                                          | 0                                                | allocator `0x31a04ba0`                                                |
| `f64`                        | input freeze status                                                                                          | 0                                                | getter `0x319f8780`                                                   |
| `f68`                        | input detachable-format state; detachable means value 1                                                      | 0                                                | setter `0x319f9a30`; getter `0x31a056b0`                              |
| `f70`                        | volatile creation timestamp; initialized from first revision stamp and self reference                        | -1                                               | setter `0x31a05ec0`                                                   |
| `f78`                        | unresolved `headerUseCode_e` domain                                                                          | 0                                                | getter `0x319f8a70`                                                   |
| `f7c`, `f80`                 | input license metadata; legal domains unresolved                                                             | 0, 0                                             | getters `0x31a052a0`, `0x31a052b0`                                    |
| `f88`                        | input replaced-component list                                                                                | null                                             | creation `0x31a04d50`                                                 |
| `bboxflag`, `bbox`           | derived pointer-presence flag and geometric bounds                                                           | absent                                           | constructor `0x31a025ec`; serializer save branch                      |
| `f98`                        | unresolved scalar                                                                                            | 0                                                | constructor `0x31a025f3`; serializer tail                             |
| `f9c`, `fa0/fa4/fa8/fac/fb0` | derived active-content bitmask and counters; adding type 2/4/8/16/32 increments its counter and sets its bit | all 0                                            | `0x31a04a40`                                                          |
| `fc0`                        | unresolved flags and version-dependent fixup                                                                 | 0                                                | constructor `0x31a02615`                                              |
| `fc4`                        | derived component count                                                                                      | 0                                                | getter `0x31a05380`                                                   |
| `fc8`                        | input copied-document state                                                                                  | 0                                                | getter `0x31a056a0`                                                   |
| `fcc/fd0/fd4`                | volatile previous open times; save uses current `fd8/fdc/fe0` when nonnegative, otherwise previous values    | all -1                                           | constructor `0x31a0264b`–`0x31a0266b`; serializer save branch         |
| `fe8`                        | unresolved `sw3DXIconOverride` enum domain                                                                   | 0                                                | getter `0x31a05100`                                                   |
| `fec`                        | derived saved-with-model flag, `int(archive.owner_model != null)`                                            | 0                                                | exact save instructions `0x31a03575`–`0x31a03586`                     |
| `ff0/ff4/ff8/ffc/f100`       | derived external-reference summary; individual meanings unresolved                                           | all 0                                            | synchronization `0x31a06210`                                          |
| `f104`                       | derived visible-sketch flags                                                                                 | 0                                                | setter `0x31a06430`                                                   |
| `f108`                       | derived annotation-presence flag                                                                             | 0                                                | setter `0x31a05f40`                                                   |
| `f10c`                       | derived graphics-feature-presence flag                                                                       | 0                                                | setter `0x31a05f50`                                                   |

**Refuted generalization:** `f08 = 24 + 2 × visible_feature_count` is not a format
rule. It is an outcome of the measured ladder's persistent-id allocation history.
Header2 and configuration ModelHeader can also have different owning-model context.
Do not copy one header's context fields into the other.

## Timestamp sentinel

The 2026 utility export `ut_getUnsetTime` in `sldutu.dll` at `0x3d03ebb0`
returns literal `0x278d00` in `eax`, then returns.
This is a utility sentinel, not a timestamp taken from a control.
The utility DLL is version `34.5.2.0604`, SHA-256
`dbc147c10b658544e44a7c13d3ae656c26a0778e9241fe74d6ca9ecae8730933`.
The [binary manifest](../v2026/Manifest2026.json) records its size and hash.
Its use as an emitted header value still needs the complete save-time rule and
target acceptance; the constructor call alone is insufficient.

## Stamps and logs

`moStamp_c` constructor `0x31a02790` takes revision status, user index, company
index and an optional comment. It stores the first three as u16 fields `f08`,
`f0c`, `f10`, takes `_time64()` for `f18`, and uses an empty comment when absent.
The default constructor at `0x31a02860` zeroes the integer fields and still
uses the current clock. These integers are not file-version numbers.

`moLogs_c` constructors `0x31a02690` and `0x31a026e0` begin with an empty
`suObList`. The parameterized constructor takes the revision-log identifier;
the default identifier is -1. Its `f50` string begins empty, but its semantic
purpose remains unresolved. Log identifiers, stamp indices and header lists
must be constructed together.

## Remaining obligations

Recover the complete enum domains, reserved-id policy, unknown flags and summary
fields, save-time timestamp rules, and log ownership relationships.
Obtain held-out vendor acceptance for a generated header with derived caches.
No field in this table authorizes copying a source control's value into a writer.
