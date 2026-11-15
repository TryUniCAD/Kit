# SOLIDWORKS 2026 biography and history construction

Status: **partial rules; generated metadata has no target acceptance**.
Byte identity on saved controls does not establish fresh metadata or a writer.

## Binary evidence

The [2026 binary manifest](../v2026/Manifest2026.json) binds these addresses:

| Routine                                             | DLL           | Address                                    |
| --------------------------------------------------- | ------------- | ------------------------------------------ |
| Biography serializer / record serializer            | `sldmodu`     | `0x4c71ec40` / `0x4c71ea50`                |
| Biography-record constructor / initializer          | `sldmodu`     | `0x4c71da70` / `0x4c720e20`                |
| Start/end constructor / serializer / initializer    | `sldmodu`     | `0x4c71db90` / `0x4c71f700` / `0x4c720ee0` |
| Version-history constructor / serializer            | `sldmodu`     | `0x4c71dea0` / `0x4c71fb70`                |
| Current-version appender / version-state serializer | `sldmodu`     | `0x4c720800` / `0x4c720030`                |
| Date-code history / state serializers               | `sldmodu`     | `0x4c71f5b0` / `0x4bb5cba0`                |
| Stamp constructor / serializer                      | `sldarchiveu` | `0x31a02790` / `0x31a048b0`                |
| Serialized time read / write                        | `swccu`       | `0x31a4bc60` / `0x31a4bcb0`                |

## Biography

The loader reads signed count `n`, reads saved records while `n > 0`, then
unconditionally creates and appends a new initialized record.
An empty persisted record list is therefore a binary-supported construction
candidate. It emits no fabricated machine telemetry. It remains unaccepted
until the complete generated document passes the oracle.

| Field                             | Role               | Rule or unresolved obligation                                                    |
| --------------------------------- | ------------------ | -------------------------------------------------------------------------------- |
| root `n`                          | derived            | `len(records)`; zero follows an explicit loader branch                           |
| record `f08`                      | derived            | target file version from the version manager; 19000 for this target              |
| record `f0c`                      | input provenance   | `su_getFullDateCode()` result for the originating build; not a geometry constant |
| record `f10`                      | constant candidate | initializer writes literal 1; generated-output acceptance remains absent         |
| record `f14`                      | volatile           | system processor architecture                                                    |
| record `f18`                      | volatile           | number of processors                                                             |
| record `f1c`                      | volatile           | OS platform id                                                                   |
| record `f20/f24/f28`              | volatile           | OS major version, minor version and build number                                 |
| record `f30`                      | volatile           | OS service-pack string                                                           |
| record `f38`                      | volatile           | user language id                                                                 |
| record `f40`, `fe8`               | derived records    | start/end telemetry structures below                                             |
| start/end `f08/f0c`               | volatile           | low/high words of system FILETIME                                                |
| start/end `f10`                   | volatile           | low 32 bits of available page-file memory                                        |
| start/end `s0/s1/s2/s3/s4`        | volatile           | system, Windows, current, TEMP and TMP directories, with trailing separator      |
| start/end `s5`                    | input/derived      | owning storage filename                                                          |
| start/end `l0` through `l5`       | volatile           | drive type for the corresponding path root                                       |
| start/end `a0,b0` through `a5,b5` | volatile           | low/high words of available free bytes for the corresponding path                |

For each `k` in 0..5, the path tuple's memory offsets are `0x18 + 0x18k`
for its string, `0x20 + 0x18k` for drive type and `0x28 + 0x18k` for
the free-space pair. The initializer calls helper `0x4c721f30` for free space.
The constructor zeroes start/end scalars and empties strings, but this does not
prove that fabricated telemetry is an accepted saved record.

## History

The version-history loader dereferences the final version state before reading
trailers. Its date-code-history loader also reads its final entry.
A zero-record biography does not imply that either history array can be empty.

| Field                 | Role                       | Rule or unresolved obligation                                                                                              |
| --------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| root `n`              | derived                    | `len(states)`, at least one                                                                                                |
| version-state `f08`   | derived stamp              | status, user/company indices, timestamp and comment below                                                                  |
| version-state `f30`   | derived                    | target file version                                                                                                        |
| version-state `f38`   | derived object             | date-code-history object for versions at least `0x178`                                                                     |
| date-code-history `n` | derived                    | `len(states)`, at least one                                                                                                |
| date-code-state `f08` | input provenance           | signed scalar; low 24 bits contain build date code; `0x01000000` is a separate save-history flag with incomplete semantics |
| root `f28`            | derived/volatile           | maximum of previous failure severity and current memory-monitor severity; constructor 0                                    |
| root `f2c`            | derived/volatile           | minimum of previous value and current minimum-free-memory reading; constructor sentinel `0xffffffff`                       |
| root `f30`            | input provenance           | maximum of previous and current license-origin classification; do not clear source provenance                              |
| root `f38`            | input/volatile             | language id; constructor 0                                                                                                 |
| root `f3c`            | unresolved flag            | constructor 0; saving CJK language ids sets it to 1                                                                        |
| root `f40`            | unresolved flag            | constructor 0; a nonzero value can warn when CJK language ids differ                                                       |
| stamp `f08`           | derived fresh-state status | appender supplies status 0                                                                                                 |
| stamp `f0c`           | derived                    | index in the same header's user-name list                                                                                  |
| stamp `f10`           | derived                    | index in the same header's company-name list; helper `0x4bf42800` finds or appends the string                              |
| stamp `f18`           | volatile                   | `_time64()` clock time, serialized in 32 bits                                                                              |
| stamp `f20`           | input                      | comment; fresh appender supplies null, producing an empty comment                                                          |

Trailer version gates use the last version state's file version.
They do not use the outer stream's path alone.
All listed trailers are present for version 19000.

The version-state loader computes its nonserialized date code as
`last_date_code & 0x00ffffff`. It appends the current build date code if the
file version matches the target and the saved code is older.
This behavior does not establish that zero is accepted as neutral provenance.

The license-origin helper `0x4c720ab0` returns 50 for maker, 40 for education,
10 for an educational serial, 20 for a student serial, 30 for a student
design-kit serial, and 0 otherwise. These are provenance categories.
They are not authorization to impersonate a vendor save or alter source licensing metadata.

## Date-code utility

The 2026 `sldutu.dll` export `su_getFullDateCode` at `0x3d0107b0` calls
`su_getTaggedDateCode` at `0x3d014520`. If tagged value `t` is in 1..99999,
the full-code function returns `t + 2000000` for `t < 9600`, otherwise
`t + 1900000`. Outside that range it returns `t` unchanged.
The tagged-code routine caches a value derived from build metadata.
Its exact originating-build representation and flag semantics remain open.

## Remaining obligations

Obtain target acceptance of a generated zero-record biography and complete history.
Recover history flag domains, telemetry-neutrality rules, complete build provenance,
and valid cross-stream user/company/log relationships.
No constructor seed in this note is a substitute for those rules.
