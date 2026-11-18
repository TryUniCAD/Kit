# Native stock sketch point slots in SOLIDWORKS 2026

Task `B04-SW2026-STOCK-SKETCH` is owned by the PR #121 takeover. It closes the shared four-line projection for the disclosed stock profile, with the through-all feature read still owned by its separate task. The input evidence was authored and reopened with `sldworks.exe` 34.5.2.0604.

| Owner | Source rule |
| --- | --- |
| `sgSketch.npoints` and `nlines` | Raw array lengths include the inactive records. The nine saves contain eight point slots and five line slots. |
| Active points | `f54 = 4`, positive `f0c` creation identity, exactly two actual line handles, and an independent `f20` reference count. The native API's point IDs combine the original slot and creation identity. |
| Inactive points | The measured local retired form has `f54 = 5`, `f0c = -1`, zero references, and two null handles. The point coordinates and remaining fields are retained as source evidence. |
| Line incidence | The line endpoint fields index the original point array. The reader resolves their live slot keys before checking exact contour ownership and endpoint handles. |
| `dims.log_g1` | Four owned unary rows use codes `4` and `5` for horizontal and vertical. Their handles select the actual live line slots. The other groups and the display list are empty in these measured profiles. |

The three independently reopened ordinary blind cuts have four native line segments and live point slots `0,1,6,7`. The same ownership is present in all three disclosed through-all designs before and after native stock depth edits. Point slots `2,3,4,5` and line slot `0` are retired in all nine saves. Repeated coordinates do not establish identity.

The [audit](../../tooling/sw2026/AuditStockSketchProjection.py) binds the earlier public source locks to nine disclosed saves and their exact native reopen observations. Nine path reads and nine in-memory reads independently match the source's line identity, endpoint slot and creation identity, endpoint positions, and horizontal or vertical axis. The first three cases go through the public strict SDK. The six through-all cases use the actual linked stock sketch with its independently validated ownership. All 108 comparisons of Config-0, ResolvedFeatures, ModelHeader, Header2, CMgr and CMgrHdr2 are byte-identical. The [process receipt](../measurements/2026/DisclosedStockSketchRead01.json) records source hashes and the SDK source fingerprint.

The public regression starts from a generated rectangle and serializes a sparse stock with a different inactive slot layout. It verifies the strict typed projection and invalid-marker and retired-endpoint rejections in separate SDK processes. The eight targeted integration tests also cover the previous dimensioned and anchored rectangles and the cache-free prism and blind-pocket paths. These are offline checks of previously reopened disclosed sources and independently generated integration inputs.
