# SOLIDWORKS 2026 empty drawing managers

The [drawing tail builder](../../tooling/sw2026/builders/DrawingTail.py) creates drawings' layer, component-property and sketch-block owners with one shared archive map. It accepts the actual generated model and sheet, authored dimension-text behavior, explicit time and target metadata, and an independently allocated block identity. Its scope is one sheet with empty layer, block and component maps.

The addresses below are from `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Remaining nonempty branches retain their provisional classification.

| Native fields | Classification and source |
| --- | --- |
| `f1430/f143c` | Active sheet pointer and initial mode word. `moDrawing_c` initializes the latter to 1 at `0x4c96b5fc`. The active pointer identifies the same object as the ordered concept list. |
| `f1444` | The constructor at `0x4c96b602` and `0x4c96b8d8` initializes bit 8. The named JIS thread-display setter at `0x4c97ce20` identifies that bit. `setAutoDimTextLink` at `0x4c97c160` writes bit 0 from an authored preference. The three controls have both bits set. Other modes select other bits and remain outside this empty profile. |
| `f1458` | Null constructor pointer at `0x4c96b617` for an empty ordinary drawing. |
| `f16a8` | `moDrwCompPropMgr_c` is allocated at `0x4c96b7d3–0x4c96b7f3`. Its constructor at `0x4c96ba20` binds the actual drawing at `0x4c96ba81` and initializes its component property map to empty. At `0x4c95ee04` and `0x4c95ee24`, the archive stores the owner pointer and entry count. |
| `f1560/f1570/f1740/f1538` | Zero derived counts for absent drawing model links and auxiliary entries. The constructor initializes the two collected model-link map counts at `0x4c96b6d4` and `0x4c96b704`, and the other collection owners at `0x4c96b8c9` and `0x4c96b67f`. |
| `f14f8` | The empty name-to-XML-stream map retains its first index value 1. Its constructor creates the empty base map and sets its tail word at `0x4c96b662–0x4c96b67c`. |
| `fed0` | The native model allocates a `moLayerMgr_c` at `0x4c01a040`. The constructor at `0x4bbe6fc0` sets the owning drawing `f30`, no active layer `f08`, and unset layer index `f38=-1`. It constructs an empty `moLayerMask_c` at `0x4bbe7011–0x4bbe705a`. The two shared native serializers start at `0x4bbe7970` and `0x4bbe7a90`. |
| `moLayerMask_c.f08` | `swccu.dll` SHA-256 `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c`, `su_CUIntArray` constructor `0x31a3dea0`, zeros the buffer, count and growth state. The empty mask has both serialized integers zero and its array length is zero. |
| `fe80`, block-map backpointer | The `moSketchBlockMgr_c` constructor at `0x4c926c50` creates an empty map and binds the manager to it through `0x4c926edd`. The map's owner points to the actual manager. Empty block and zero-instance lists derive from the requested sheet content. |
| `moSketchBlockMgr_c.f380` | Volatile GUID. The fresh constructor passes the member to `CoCreateGuid` at `0x4c926efc–0x4c926f03` and stores 16 bytes at `0x4c90b246`. The caller supplies a fresh UUID4 and the writer uses Windows little-endian field ordering. [Template GUID gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingBlockManagerAllocatesGuid.md) |

The [tail process](../../tooling/sw2026/serial/CheckDrawingTail.py) verifies the released drawing controls' backpointers and class fields. It also creates two independent tail graphs with different dimension-link options from authored data and an independently authored test identity. Their measured 322-byte archive subgraphs load with matching map counters and all four pointer aliases. [Tail receipt](../measurements/2026/DrawingTailFields01.json)

The tail subgraph gets closer to the complete drawing Definition. The actual sheet's support nodes, drawing-specific UI preferences and separately stored caches still need construction or native absence evidence. [Sheet construction](DrawingEmptySheetConstruction2026.md)
