# Ordinary external reference serialization in SOLIDWORKS 2026

The ordinary version-19000 assembly stores the external reference name as a pooled `moCStringHandle_c` object. The external feature adds one nullable archive reference tag and a signed 32-bit integer. This proof covers the disclosed ordinary resolved component records and the wire boundary used by planar mate endpoints. The direct CString alternative and historical pattern-data load are partial findings. [Ordinary occurrence records](OrdinaryOccurrenceConstruction2026.md) · [Planar projection](PlanarMateProjection2026.md)

The pinned build is SOLIDWORKS 2026 SP05.2, `34.5.2.0604`. Addresses are preferred PE virtual addresses. The 2026 serializer map identifies `0x4c178a30` under `moExtFeature_c` and `0x4c179410` under `moGFR_c`. The latter is also the direct interface call inside `moExtFeature_c` at `0x4c178a98`. [2026 serializer map](../../data/Serialization/SerializeMap2026.json)

| Module | SHA-256 |
| --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldmfcu.dll` | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` |
| `sldarchiveu.dll` | `5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48` |
| `swccu.dll` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |

## Interface body at `0x4c179410`

| Order | Field | Wire rule | Store and load evidence |
| --- | --- | --- | --- |
| 1 | `f10` | Inline `moSharedFileDef_c`. The load hashes the file definition into the interface. | Virtual serializer at `0x4c17945a`. The current reader loads the temporary and hashes it at `0x4c179500` and `0x4c179510`. The inline load starts at version `0xf25`. |
| 2 | `f18` | Inline `moReferencedConfiguration_c`. | Virtual serializer calls at `0x4c179467` and `0x4c179520`. |
| 3 | `f40` | One byte written from the member. The reader normalizes nonzero to `1`. | `0x4c179471`, `0x4c17952a`–`0x4c179539`. |
| 4 | `f44` | Signed 32-bit persistent feature identifier. | `0x4c17947d`, `0x4c179633`–`0x4c17963c`. |
| 5 | `f38` | One typed `moCStringHandle_c` archive object in the ordinary current path. It contains the name. | Store gets the pooled handle from the string manager at `0x4c1794a8` and writes it at `0x4c1794b9`. Load reads it at `0x4c179684` and copies its internal CString. The handle overloads use typed `WriteObject` at `sldmfcu!0x3c7c796e` and typed `ReadObject` at `sldmfcu!0x3c7c792b`. |

The name branch tests the live `sldmodu` byte `0x4db84749` at `0x4c179487` on store and `0x4c17964a` on load. Zero selects the handle path on store. Zero and an archive version of at least `0xaa9` select it on load. Nonzero selects the direct CString overloads at `0x4c179493` and `0x4c1796c7`. The PE section places this byte in the zero-fill tail of `.data`. A linear `.text` sweep found both direct compares and no direct setter. The default and disclosed ordinary path agree. The nonzero mode's runtime caller remains open.

## External feature suffix at `0x4c178a30`

| Field | Wire rule | Store and load evidence |
| --- | --- | --- |
| Interface body | Serialize it first in either direction. | `0x4c178a98`. |
| `f50` | One ordinary object tag with a nullable `moReference_c` derivative. The native current store always writes the tag. | `su_CArchive` object store at `0x4c178c46`. The reader consumes the tag from version `0x92` at `0x4c178cb7`. Nonnull objects pass `moReference_c` runtime class validation at `0x4c178cc4`–`0x4c178ce1`. |
| `f58` | Signed 32-bit pattern owner identifier. The ordinary nonpattern constructor uses `-1`. | Store at `0x4c178c53` and load from version `0x11eb` at `0x4c178dde`. The constructor seeds `-1` at `0x4bac8f93`–`0x4bac8f98`. Its pattern route calls `getPatternOwner` at `0x4bac8fb4` and uses that owner's `getID` at `0x4bac8fc4` or the reference's stored `+0x568` value at `0x4bac8fce`. |

Before storing the interface, a live `f50` refreshes the name and identifier through `0x4c178a79` and `0x4bacafa0`. Main vtables for `moReference_c` and `moReferenceInternal_c` at `0x4cf7a8b0` and `0x4cf7e430` bind these calls to `moFeature_c::isDeleted(nullptr)` at `0x4bb4ac90`, `moFeature_c::name` at `0x4bb4d460`, and `moNode_c::getID` at `0x4b283ba0`.

The ordinary no-view store route keeps `f50` when it is present, live and owned by the archive's filed document. The owner comparison is `0x4c178c20`–`0x4c178c39` and uses `moFeature_c::getFiledOwner` at `0x4bb44300`. Earlier guards select null for deleted references, `moReferenceBrowser_c`, or the no-view archive with a condition matching `0x02006201`. `sldmfcu!0x3c7ac130` implements the condition test as a bitwise intersection. Disclosed A13 and A14 each show the Config-0 live occurrence backlink and the CMgr null tag. [Occurrence ownership](OrdinaryOccurrenceConstruction2026.md#archive-ownership)

The reader separately consumes a historical `moExtFeatPatData_c` tag in the half-open version range `[0x9fa, 0x105e)`. A nonnull object supplies its signed 32-bit member at `+0x10` to `f58`. The current profile skips the whole branch at `0x4c178d3f`–`0x4c178d45`. The older interface body, pattern-data object and drawing-view filters remain outside the ordinary scope. [Existing archive rules](../../tooling/sw2026/serial/defs/VisualRefs.py)

The disclosed occurrence observations and planar projection corroborate the current pooled layout and reference ownership. This static trace adds no generated or held-out run and changes no writer behavior. [Disclosed planar projection receipt](../measurements/2026/PlanarMateProjection02.json)
