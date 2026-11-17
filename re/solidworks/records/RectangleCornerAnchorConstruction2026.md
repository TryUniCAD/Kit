# SOLIDWORKS 2026 corner anchor construction

The shared part builder accepts the research option `rectangle_anchor="corner"` for one dimensioned Front Plane blind boss whose first authored vertex is the part origin. The part still uses the ordinary four-edge contour to construct the body. The anchor is attached to the sketch after contour binding. Its external point is a separate sketch entry. [Builder](../../tooling/sw2026/builders/RectangleAnchor.py) · [Source controls](RectangleAnchorSources2026.md)

The constructor evidence is from `sldmodu.dll` version 34.5.2.0604 with SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The addresses use that PE's preferred base. The supplied wrapper constructor sets the external entity's live reference and clears unused links. The selected sketch handle uses the regular unit-component constructor and the point-handle clone. The sketch operation creates a type-6 external point with the selected link and makes it permanent. The two-point logical-dimension constructor supplies both handle records and initializes the optional branches.

| Constructor range | SHA-256 of address range | Used rule |
| --- | --- | --- |
| `[4c434f70,4c434fc5)` | `c51b5f04034df943df877391ebe1f5a9d278603f32352c739a8c5b259126ba48` | `sgExtEnt_c` assigns the provided wrapper and clears three inactive links |
| `[4b7e8750,4b7e88a1)` | `f9d7f12038c43da25034f2970444fa0752b998b81a2d9312f66f5e1ab49937f4` | The component selection binds a unit-component owner and clones the selected point handle |
| `[4c700fb0,4c701121)` | `3af655fe414951418c6577069c88b34c5db74b30c3e651906aad56206001a216` | The external point receives its position and type, is inserted into the point collection and takes the permanent flag branch |
| `[4c410460,4c410570)` | `0a03c7cf7147afe9d604c785256b42491b97ed2dff36728ba05e7347440a92c4` | The binary relation constructor copies both supplied handles, sets the negative optional selectors and clears unused state |

| Owner and field | Classification | Construction and scope |
| --- | --- | --- |
| Boundary point and length text positions | Input | The first boundary vertex must be at the actual model origin in the Front Plane frame. The ordinary dimensioned rectangle continues to own the width and height. |
| Origin point `f08` and `f0c` | Derived | Assign the origin's allocated permanent point mark as its persistent identity when it becomes a reference target. Its single native local point slot is zero. |
| `moCompSketchEntHandle_c.ff0`, `f0f8`, `f100` | Derived | Bind the actual Origin feature ID and its creation time, a handle scoped to that origin sketch, and the same permanent point mark. Clone the self component with the same part owner. |
| `moSketchExtRef_w.f58`, `fb8` | Derived | Hold the selected point handle and back it with the actual origin position transformed by the origin profile frame. |
| `sgExtEnt_c.f08`, `f28` | Derived | Hold the wrapper and form the native `Point{ordinal}@{origin name}` label from the selected point and profile. |
| `sgExtEnt_c.f10/f18/f20`, `moSketchExtRef_w.fb0` | Constant | Inactive constructor branches carry null objects or zero in this point-only profile. |
| External point position, `f0c`, `f54`, `fe4` | Derived and constant | The point at local zero follows the authored origin. The ordinal is one plus the number of existing sketch points. Clear the two transient low flags for the permanent point. Type 6 identifies the external point. |
| `sgLogG2Dim.f80`, `h1`, `h2` | Constant and derived | Type 9 is the observed origin coincidence. Handle one owns the new external point and handle two owns the actual boundary corner. Both use the sketch's generated point order. Their reference counts advance once. |
| `sgLogG2Dim.f90`, `fa0`, optional links and selectors | Constant | The two-point branch uses two operands, native `0xfffe` initial state, null inactive links and the negative optional selectors. |
| `sgSketch.f188` and auxiliary coincidence maps | Derived | The validated external selection belongs to the same part. The logical dimension list owns the relation and there is no intercomponent reference or separate coincidence record in the exercised source profile. |
| Wrapper flags, selected-component activity and solver status | Volatile | The discovery uses known fresh constructor state. The later native publication and solver updates require further measurement. |

Two isolated guarded builds used the same frozen 4,590-file closure and produced identical 8,289-byte artifacts with zero runtime input reads. All eight non-XML streams round-tripped byte for byte with Config seeding the resolved map. The additional reference and relation add 576 bytes to the resolved stream and 12 archive map slots for this model. The same source without the anchor is identical to a separate build through the prior shared builder. Centered or off-origin requests fail before emitting a file. [Guarded receipt](../measurements/2026/GeneratedRectangleAnchorGuard01.json)

The [disclosed native observer](../../tooling/sw2026/InspectGeneratedRectangleAnchor.py) compared the generated model to its independently authored source. The original and both independently edited siblings retained constraint state 3, all seven native relations, the same ordered 25-row feature tree, three driving dimensions and one solid. The source and candidate agreed in 165 numeric checks covering model geometry, volume, area, mass and centroid. Both edited files saved cleanly and retained their relation bindings and geometry in a fresh process. Both pristine controls passed across six distinct oracle processes. [Native receipt](../measurements/2026/GeneratedRectangleAnchorNative01.json)

This disclosed result qualifies the fresh constructor and solver state for this one corner model. Centered construction and the two pre-writer held-outs remain open.
