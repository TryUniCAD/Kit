# Owned centre fixation in an ordinary blind-pocket sketch

The all-bodies candidate is Kit-generated and was accepted in the controlled SOLIDWORKS 2026 SP05.2 batch. Its SHA-256 is `340e52b7ca4acca96b977bb5f514eb361323a560a69e44c067801c91b4253b12`. The independent typed read of its 18,968-byte `Contents/Config-0-ResolvedFeatures` stream used the owning Config-0 map, base 82, and consumed the whole stream. The stream SHA-256 is `a76fa074b7bcea3a20b4c1c7a29cf2aef1a142750c830fab07b6f9c3231507b4`. These offsets identify the inspected specimen. The SDK derives its offsets from parsed structure. [Native batch](../measurements/2026/GeneratedBlindPocketNative02.json) · [Generated graph](OrdinaryBlindPocketSynthesis2026.md)

| Record | Half-open byte span | Owned data |
| --- | --- | --- |
| Origin sketch class declaration | `[4541,4555)` | `sgSketch` class 132. The sketch object then takes index 133 before its body begins. |
| Origin logical-one record | `[4759,4831)` | Fixed type `0x11`. The new class at 4802 allocates `sgPointHandle` at 134 and its object at 135. The handle selects its own origin point slot 0. |
| Origin display list declaration | `[4845,4859)` | `suObList` class 136, after the absent logical, pattern and iso lists. |
| Pocket sketch class reference | `[14253,14255)` | A fresh sketch object uses the same `sgSketch` class 132. |
| Pocket point and arc arrays | `[14255,14696)` | Two points and a circular arc. The type-zero centre is point slot 0 at `(9.7, -7.3)` mm. Both arc endpoints reference the type-two seam in slot 1. The arc separately references centre slot 0. |
| Pocket value dimension body | `[14747,14904)` | `sgCircleDim` type 3, own arc handle and driving length parameter `D1` at 6.41 mm. |
| Pocket logical-one record | `[14912,14967)` | Fixed type `0x11` and no parameter, tolerance or attachment. The class reference at 14955 uses class 134 to instantiate a new `sgPointHandle` at index 210. Its compact local point is slot 0, block `-1` and external key 0. |
| Pocket display list reference | `[14981,14983)` | Class 136, aligned after the same seven absent lists as the origin. |

## Reader proof and scope

The parser bounds the origin within the typed origin feature and the circle within the current profile. It requires the ordinary nonreused profile fields before each sketch tag. The verified origin path admits one type-one point with no object-bearing optional fields, no value dimension and one fixed logical record. Allocating a class and its object consumes two successive map slots, so the first `sgPointHandle` declaration lies two slots beyond the origin's sketch class. Its following display list class lies two further slots away. The ordinary circle uses the class reference at its verified geometry-array start and checks both predicted references in their role-specific positions.

Sketch arrays establish the centre and seam slots. The decoder walks the ordinary radial prefix through its declared `sgCircleDim` class, the existing named scalar position and value, and the local handle forms. The independent typed archive inspection resolves the length and arc classes in the specimen. The bounded reader uses their ordinary field layout and existing radius anchor to reach the logical list. The radius retains its existing parameter binding. Logical operand ownership follows the independent point-class proof. The fixed relation's own reference must have the proven point class and select the circle's distinct local centre. The complete relation extent becomes its source provenance. [2026 logical point grammar](CircleCenterFixation2026.md) · [Archive map construction](ArchiveMapConstruction2026.md) · [Shared sketch schemas](../../tooling/sw2026/serial/defs/ResolvedSketch.py)

This is a readback rule for the admitted 2026 shape with one local radius dimension and a single logical point relation. It requires the first seam-handle, radial and unused-handle declarations in the accepted span and excludes reused profiles, additional relations, block or external handles and unsupported variable fields. Its scope is SDK readback from an independently generated document. The pre-existing application's native acceptance applies to the generated specimen. The new SDK change has separate local readback evidence. [SDK change](../../../Documentation/Changes/Solidworks/Inspection/Sketches/SolidworksPocketCenterFixation.md)

The public SDK returned the radius and the fixed point as two separate relations for the native-verified generated file. The first has the driving parameter `D1`. The second targets `center` on the same circle and retains its 55-byte provenance. The circle entity's fixed flag is clear. [SDK receipt](../measurements/2026/GeneratedBlindPocketFixedCenterSdk05.json)
