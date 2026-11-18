# Complete SDK blind-pocket construction

Task `B04-SW2026-CUT` is owned by root and delivered in PR #121. The constructor builds the ordered rectangle, boss, circle and cut from one neutral document with one active configuration. It uses the shared version-19000 archive codecs and the measured current `moICE_c` class grammar. [Linked archive rules](OrdinaryBlindCutConstruction2026.md#linked-sdk-archive)

| Owner | Class or rule | Origin |
| --- | --- | --- |
| Neutral geometry and dependency | One rectangular region and one interior circle on the actual Front Plane. The cut consumes the preceding boss. Its depth is smaller than the boss. | Authored geometry and feature history |
| Circle constraints | A driving radius or diameter owns an actual circle and its fixed centre. An undimensioned circle retains its free sketch records. | Authored sketch relations |
| `moICE_c` and `moEndSpec_c` | Shared ordinary extrusion constructors allocate the actual cut class, sketch dependency and sole forward distance display. The cut contributes operation `1`, reverse flag `1` and the bound operation mask. | Native command rules and modeled depth |
| Body and chooser state | The ordinary all-bodies cold lane uses scope word `0`, constructor-empty body lists and no chooser. | Prior controlled cold rebuild proof |
| Map and metadata | Persistent IDs come from the shared allocation sequence. The linked map extends the actual Config-0 map. KeyWords links the cut to its actual sketch ID and formats its owned length in presentation units. | Derived from the constructed part |

The [neutral fixture author](../../tooling/sw2026/AuthorSdkPocketInputs.py) supplies three independent geometries and analytic volume, area and centroid predictions. The [audited worker](../../tooling/sw2026/SdkPocketProcess.py) receives each portable document by standard input. Separate workers build twice and read, re-emit and repack every generated stream. They verify the exact feature and dimension owners and the actual keyword child link. The construction phase preloads SDK code and denies runtime file reads and subprocesses.

| Disclosed design | Circle mode | Resolved bytes with boss only | Resolved bytes with cut | Linked map counter with cut |
| --- | --- | ---: | ---: | ---: |
| SdkPocketA | Radius | 13,865 | 18,769 | 235 |
| SdkPocketWideBeta | Diameter | 13,865 | 18,787 | 235 |
| SdkPocketFree | Free circle | 13,865 | 16,976 | 222 |

The three builds repeat exactly, 30 stream comparisons pass, and six malformed or unprojected inputs reject. Both earlier dimensioned requests reproduce their original bytes after adding the free-circle path. The process receipt binds input, output and source hashes. [Process receipt](../measurements/2026/SdkBlindPocketProcess01.json)

## Disclosed native lifecycle

Each generated part opened with one solid before explicit rebuild, with zero open errors and warnings. The cut reported the actual preceding boss as a parent. Each of the three cut-depth edits rebuilt with zero native errors or warnings and survived a save and fresh reopen. The radius and diameter edits rebuilt independently and preserved the live drivers after restoration. The free circle retained an undimensioned sketch. The observer compares native geometry to the rectangle-minus-cylinder prediction.

All three batches pass 275 numeric checks across 12 fresh processes with six healthy controls. Config-0 and ResolvedFeatures re-emit exactly from each native-edited file. The receipts bind the original measured tooling. In those raw per-phase files the terminal outcome is `result.passed`. The recorder now mirrors that value at the top level for subsequent runs.

The public portable read still reports the multi-operation typed projection boundary on these histories. The two earlier locked source parts remain reserved for the original held-out comparison after semantic projection. [Native receipt](../measurements/2026/SdkBlindPocketNative01.json) [Original source locks](../v2026/heldout/OrdinaryBlindCutSourceLock.json)
