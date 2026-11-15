# SOLIDWORKS 2026 standard-view construction

Status: **signed native construction and wire rules recovered; the corrected negative-half-angle generator awaits native remeasurement**

The earlier generated model wrote ten null `moView_c` entries in its `f9f8`
array
The native loader replaces each null with an identity-view constructor, assigns
its index and reloads its name, without computing its canonical orientation
The missing constructor lifecycle explains why a named isometric target can
remain a front orientation even when the part has a healthy solid body
Native acceptance of a generated repair, and initial active-camera behaviour,
remain separate obligations

The oracle owner's viewport observation is reported context, not a measurement
performed or independently inspected here
This work read native binaries and existing private static analyses only
No vendor document stream, held-out native stream or saved field values supplied
any of the constants or formulas below
No CAD process, repository module or local test was executed
The static investigation changed no writer code; the shared generator described below was implemented afterward

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md),
[reverse-engineering book](../../Playbook/README.md) and no-donor standard apply
Their acceptance conditions are not satisfied by this static record
The criteria's stopping conditions remain “success under every criterion on this
page” or “the end of the available context”

## Critical correction: the native half-angle is negative

The first revision of this record incorrectly treated the axis-angle helper's
half-angle factor as positive without reading its referenced constant
That positive-half-angle assumption is **refuted**
The first view construction following it produced a numerical orientation
mismatch despite successful native loading and a nonempty body

Instruction `sldmgu!0x31f0fa84` multiplies the incoming angle in `xmm7` by the
binary64 at preferred address `0x31f46ff0`
Direct inspection of that operand gives value `-0.5`, IEEE-754 bits
`0xbfe0000000000000`
The following cosine and sine calls consume this negative half-angle
Consequently the native rule is
`Q(axis,a)=(axis*sin(-a/2),cos(-a/2))`, with the vector's three components
expanded separately
Keep the documented angle constants, Hamilton multiplication order and matrix
layout unchanged
The owning correction is in axis-angle construction, not a transpose or sign
patch fitted to a measured matrix

The oracle owner's negative comparison is
[committed negative comparison](../measurements/2026/PolygonViewSignMismatch.json),
original `Oracle121Takeover/Rotations417d/Rotations.json`, raw SHA-256
`a75ba4f5f78d74690c33b0f501c6e0ee0c5f10b5e1bee8f16dafc392b6de1f36`
Its authority is `native-visible-document-viewport`
Both controls and the candidate have one body; the owner reports healthy,
unchanged inputs in all three rows
Their active-view orientation after standard view seven exposes the sign
difference; the report's separate standard-view helper raised `ArrayData`
because the API returns a tuple, so that failed helper supplies no standard-view
matrix evidence
These measurements prompted the native operand read but do not supply writer
values
Fresh native measurement of the corrected construction is still required

## Binary and evidence binding

Addresses are preferred virtual addresses, not process addresses or stream offsets
The installation is SOLIDWORKS 2026 SP05.2, build `34.5.2.0604`
Hashes were recomputed from the private binaries

| Module        | Preferred base | SHA-256                                                            |
| ------------- | -------------- | ------------------------------------------------------------------ |
| `sldmodu.dll` | `0x4b140000`   | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldmgu.dll`  | `0x31dd0000`   | `99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c` |
| `sldresu.dll` | `0x404e0000`   | `531cf5d1c913f60f707652f0ecae600313d0970f7e649dcadec64983c484e111` |

The [2026 manifest](../v2026/Manifest2026.json) binds the model and geometry DLLs
The resource DLL was read directly for its language `0x409` string resources
Existing private `gh/out/cl_sldmodu.c`, `gh/out/small_refs_4daf11b8.c` and
`gh/out/sldmodu_vtslots.txt` supplied initial method locations
Instruction disassembly and direct PE reads checked the conclusions
No vendor listing or binary is distributed with this record
Vendor strings and code were treated as untrusted data

PE inspection used explicit sufficient import/export budgets when resolving
the complete relevant symbol directories
The PE parser reports 198 model-DLL and 17 geometry-DLL chained-unwind warnings
These are not import/export truncation claims
The audited methods below were decoded from established entries through their
returns; a missing unwind fragment was not used to infer a missing operation
Their hashes bind the stated half-open image-byte ranges and do not hash
transitive callees

| Module   | Method or role                   | Start        | End, exclusive | Range SHA-256                                                      |
| -------- | -------------------------------- | ------------ | -------------- | ------------------------------------------------------------------ |
| Model    | `setDocumentDefaultViews`        | `0x4c0352c0` | `0x4c0355ca`   | `b72967a76879592dfba1c87fa28402ea59085467a91aa103780c568e50b2c50c` |
| Model    | Apply canonical transforms       | `0x4c031d10` | `0x4c031e19`   | `b768bcabfef4a553a8853db1eaa4d48ba6fce3090454eb80326c3f98b9450e6b` |
| Model    | Compute ten transforms           | `0x4c0331f0` | `0x4c033887`   | `233e880efb362aad6ad2a092b90b9adfeeefe22883a217ab4a7ae1cb8509af64` |
| Model    | Restore localized names          | `0x4c031b40` | `0x4c031d01`   | `705b0793cf0bf2403fbe80e0c05fddb52809dbe85328fb52a411e4a6098a4098` |
| Model    | Indexed view constructor         | `0x4c14fb90` | `0x4c14fcd7`   | `c190109ccf11364497744fc07c353b063596310dacf0ef75c2d83e180609b777` |
| Model    | Loading/default view constructor | `0x4c14fce0` | `0x4c14fdff`   | `cb7464836b1bc67f5ef5b115e0841072f8ce6267fdc3e52154564eed221b49e5` |
| Model    | `moView_c::Serialize`            | `0x4c22c9d0` | `0x4c22d028`   | `dd858d51e82d3ff05842ef4a0c0ef1d31ff3e6cf26a34f7813247abde0ccb439` |
| Geometry | Axis-angle quaternion            | `0x31f0fa20` | `0x31f0faed`   | `6e7d548ca49348218cb2e20e6fbce25ccdc43f8594f02bf1bbdc2e5aee3c1811` |
| Geometry | Quaternion multiply              | `0x31f0f2c0` | `0x31f0f3f3`   | `a9e6f9c204b49d3115d61a22930999d62921012930ef1a42f9d1f93778625a86` |
| Geometry | Quaternion multiply/assign       | `0x31f0f400` | `0x31f0f43d`   | `8094f1401b3d34d32ef4fa68a817da3466dd27850eb5fdfc480ffc6ca3e5fe35` |
| Geometry | Quaternion to matrix             | `0x31f0fe00` | `0x31f0fff9`   | `2f9de41bfc93a11dbff676cc39f3554634777191000a6cc6afef9217945128ed` |
| Geometry | Unit-vector constructor          | `0x31f19110` | `0x31f191b9`   | `5616176f0e3e9b36283bafe6da1d0a21e35a6a60052e3fb34d27304a52c8d539` |
| Geometry | Matrix from three vectors        | `0x31e26880` | `0x31e2696e`   | `68c3a9a7a8dcd6ba6691322edd08de5684b8c19f9e39c3bb2b395642207cd3a7` |
| Geometry | Matrix constructor wrapper       | `0x31e26c10` | `0x31e26c92`   | `a0802cc9cc7028766743554ca312868356ae41cd5b931800cffad0bad78bbce6` |
| Geometry | `mg_RestoreXform`                | `0x31f23ed0` | `0x31f23ff5`   | `6f486ff6da66512da2fd1d146355a8aa34d790bc499f0ac458112423057ec959` |
| Geometry | Matrix save                      | `0x31e039b0` | `0x31e03a12`   | `5bc107870e8e4ea71777c5ce13c49f229f337af22a583550324cd521478cd31f` |
| Geometry | Transform save                   | `0x31e03ce0` | `0x31e03d9a`   | `5f1688c25be1fb61cdc6897d2b6816971f5db014222a59482cbdfaa8e1eb23e1` |

## The missing lifecycle

`moModel_c::setDocumentDefaultViews` at `0x4c0352c0` allocates ten distinct
objects of size `0x3d0`, calls indexed constructor `0x4c14fb90` with view numbers
zero through nine, and stores them consecutively at model `+0x9f8..+0xa40`
That constructor supplies names and IDs but initially creates two identity
transforms for every view
Allocating indexed views without the following step would still lose orientation

At `0x4c03558d`, the initializer calls model virtual `+0x15d0` with argument zero
For the inspected model, part and assembly vtables, that slot is `0x4c031d10`
It constructs ten transforms, calls generator `0x4c0331f0` with that zero flag,
and then copies each transform into its view's `+0x368` through `0x4c150c70`
It separately copies identity into view `+0x370` through `0x4c150c80`

The loading path is `moModel_c` serializer body `0x4c234150`
Its current-version loop reads ten `moView_c` object references at model `+0x9f8`
For a null reference it allocates a view using default constructor `0x4c14fce0`
That constructor creates two identity transforms and sets its initial view ID
to `-1`
The load loop then overwrites the ID at view `+0x360` with the array index
Its final model virtual `+0x1880` resolves to `0x4c031b40`, which only assigns
the localized names at each view's `+0x358`
It does not call the transform generator or replay virtual `+0x15d0`
Thus null wire entries retain identity orientations in this path
This dataflow is **confirmed static**, independently of viewport observations

## Class and active wire grammar

`moView_c::GetRuntimeClass` at `0x4c20f010` returns record `0x4daf18a8`
Direct reads give class name `moView_c`, object size `0x3d0`, raw schema
`0x80000001`, and factory `0x4c20f710`
The factory calls default constructor `0x4c14fce0`
Use wire schema one for a tagged view object

The active definition is the nonprovisional `moView_c` definition in
`re/tooling/sw2026/serial/defs/SmallCMgr.py`
Although the runtime class has a larger inherited object layout,
`moView_c::Serialize` calls `su_CObject::Serialize` and does not serialize a
`moFeature_c` or node base payload here
Do not add a model persistent ID, node-name object or owner reference to this
view wire record

The model schema in `serial/defs/ConfigPart.py` serializes `f9f8` as exactly
ten tagged object references at the current version
Every generated view must be a distinct object
The two transforms are embedded field payloads in each view record

| Wire fields, in current order | Classification                    | Generative rule                                                     | Native evidence                                      |
| ----------------------------- | --------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------- |
| `f358`                        | Format vocabulary/localized input | Canonical resource name for the array index; resource mapping below | `0x4c0352c0`, `0x4c031b40`, constructor `0x4c14fb90` |
| `f368`                        | Derived                           | Canonical orientation transform computed below                      | `0x4c031d10`, `0x4c0331f0`                           |
| `f370`                        | Constructor/initializer constant  | Identity transform                                                  | `0x4c14fb90`, assignment `0x4c031db3`                |
| `f388`                        | Constructor constant              | u16 zero                                                            | `0x4c14fc60`; serializer `0x4c22c9d0`                |
| `f38c`                        | Constructor constant              | i32 `-1`                                                            | `0x4c14fc67`                                         |
| `f378`                        | Constructor constant              | f64 `-1.0`                                                          | `0x4c14fc48..0x4c14fc52`                             |
| `n380`, `f380`                | Derived absent optional array     | i32 zero and empty items; native pointer at `+0x380` is null        | `0x4c14fc59`, store path `0x4c22c9d0`                |
| `f360`                        | Derived                           | i32 array index `0..9`; loader also enforces this index             | `0x4c14fbda`; model load loop `0x4c234150`           |
| `f394`                        | Constructor constant              | i32 zero, upper half of zero qword at view `+0x390`                 | `0x4c14fc71`                                         |
| `n398`                        | Derived absent optional list      | Explicit i32 zero; omit embedded `f398` payload                     | `0x4c14fc78`; serializer's null-list branch          |
| `f3a8`                        | Constructor constant              | i32 zero                                                            | `0x4c14fc86`                                         |
| `f3b8`                        | Constructor constant              | f64 zero                                                            | `0x4c14fc94`                                         |
| `n3b0`                        | Derived absent optional list      | Explicit i32 zero; omit embedded `f3b0` payload                     | `0x4c14fc8d`; serializer's null-list branch          |
| `f3c0`                        | Constructor constant              | i32 zero                                                            | `0x4c14fc9b`                                         |
| `f3c8`                        | Constructor constant              | i32 zero                                                            | `0x4c14fca2`                                         |

These rules are **confirmed static** for ordinary default views without section
data or view-specific object lists
The active `Flag` fields require explicit `n398=0` and `n3b0=0`
Omitting the keys is not equivalent to encoding the native absent-list branch
Runtime `+0x3c4` is loader context state and has no separate field in this grammar

## Canonical name and index vocabulary

The following English strings were decoded from `sldresu.dll` `RT_STRING`,
language `0x409`, at the exact IDs used by the constructor and name-restoration
method
They are compiled vocabulary, not values copied from a saved CAD document
Other installed languages require their corresponding resource vocabulary

| Array index / view ID | Resource ID | Name         |
| --------------------- | ----------- | ------------ |
| 0                     | `0x2938`    | `*Normal To` |
| 1                     | `0x2939`    | `*Front`     |
| 2                     | `0x293a`    | `*Back`      |
| 3                     | `0x293b`    | `*Left`      |
| 4                     | `0x293c`    | `*Right`     |
| 5                     | `0x293d`    | `*Top`       |
| 6                     | `0x293e`    | `*Bottom`    |
| 7                     | `0x293f`    | `*Isometric` |
| 8                     | `0x2e2a`    | `*Trimetric` |
| 9                     | `0x2e2b`    | `*Dimetric`  |

## Exact angle constants

All angles are radians loaded by instructions in `0x4c0331f0`
Decimal values below use round-trip 17-significant-digit formatting
The IEEE-754 binary64 bit patterns are authoritative when the shortest decimal
contains fewer printed digits
Do not substitute `math.pi`, an ideal isometric angle, a rounded degree value or
a coefficient fitted from a saved matrix

| Symbol    | Model-DLL address | Exact binary64 bits  | Decimal value          |
| --------- | ----------------- | -------------------- | ---------------------- |
| `P`       | `0x4cdd14b8`      | `0x400921fb54442d28` | `3.1415926535898002`   |
| `H`       | `0x4ce10698`      | `0x3ff921fb54442d28` | `1.5707963267949001`   |
| `NH`      | `0x4ce7f270`      | `0xbff921fb54442d28` | `-1.5707963267949001`  |
| `IY`      | `0x4d0c9170`      | `0xbfe921fb54442d28` | `-0.78539816339745006` |
| `IX`      | `0x4d0c9158`      | `0x3fe3b161d47596ef` | `0.61540309425319417`  |
| `TY`      | `0x4d0c9168`      | `0xbfdf1342d0a37aab` | `-0.48555059790479999` |
| `TX`      | `0x4d0c9150`      | `0x3fe1504c6d4006d3` | `0.54105206811819995`  |
| `DY12`    | `0x4d0c9160`      | `0xbfd720a392aa03d0` | `-0.36136712382000002` |
| `DX12`    | `0x4d0c9148`      | `0x3fd5bfe34eedf184` | `0.33983690937`        |
| `DXother` | `0x4d0c9140`      | `0x3fd15bbc9a74b6bd` | `0.27122416575989999`  |

## Quaternion construction and multiplication order

The supported initializer call passes flag zero to `0x4c0331f0`
At `0x4c033268`, that selects identity base quaternion `B=(0,0,0,1)`
A nonzero flag instead derives a base quaternion from an inverse axis matrix;
that alternate convention is outside this reconstruction

Let `Q(axis,a)=(axis.x*sin(-a/2),axis.y*sin(-a/2),axis.z*sin(-a/2),cos(-a/2))`
`mg_RotationQuaternion` at `0x31f0fa20` normalizes the supplied axis, multiplies
the angle by negative one half using constant `0x31f46ff0` at instruction
`0x31f0fa84`, calls cosine at `0x31f0fa8f` and sine at `0x31f0fa9a`,
then stores vector components at offsets `0/8/0x10` and the cosine at `+0x18`
The helper has a small-angle identity branch, but every nonzero canonical angle
listed here takes the trigonometric branch

`mgQuaternion_c::operator*` at `0x31f0f2c0` is Hamilton multiplication
For `a=(ax,ay,az,aw)` and `b=(bx,by,bz,bw)`, its operation grouping is:

```text
x = ((ax*bw + bx*aw) + ay*bz) - az*by
y = ((by*aw - bz*ax) + ay*bw) + az*bx
z = ((by*ax + bz*aw) - ay*bx) + az*bw
w = ((bw*aw - ax*bx) - by*ay) - az*bz
```

Multiply/assign at `0x31f0f400` calls that multiplication and copies the four
result doubles back into its left operand
For the compound views, `0x4c0331f0` resets a working quaternion to `B`, applies
the Y-axis rotation, then applies the X-axis rotation through this multiply/assign
operator
Consequently the composition is `(B * Q(Y,y)) * Q(X,x)`, in that order
Do not silently exchange it for `Q(X,x) * Q(Y,y)` or transpose the final matrix

| Index                     | Quaternion used for orientation    | Generator evidence                                             |
| ------------------------- | ---------------------------------- | -------------------------------------------------------------- |
| 0                         | Identity transform copied directly | `0x4c033239..0x4c033243`                                       |
| 1                         | `B`                                | conversion at `0x4c0332ff`, store at `0x4c033334`              |
| 2                         | `B * Q(Y,P)`                       | Y angle load `0x4c03334e`, store `0x4c0333b6`                  |
| 3                         | `B * Q(Y,H)`                       | Y angle load `0x4c0333d0`, store `0x4c033438`                  |
| 4                         | `B * Q(Y,NH)`                      | Y angle load `0x4c033452`, store `0x4c0334ba`                  |
| 5                         | `B * Q(X,H)`                       | X angle load `0x4c0334d4`, store `0x4c03353c`                  |
| 6                         | `B * Q(X,NH)`                      | X angle load `0x4c033556`, store `0x4c0335be`                  |
| 7                         | `(B * Q(Y,IY)) * Q(X,IX)`          | multiply/assign `0x4c033603`, `0x4c03362d`; store `0x4c033668` |
| 8                         | `(B * Q(Y,TY)) * Q(X,TX)`          | multiply/assign `0x4c0336ad`, `0x4c0336d7`; store `0x4c033712` |
| 9, effective field 1 or 2 | `(B * Q(Y,DY12)) * Q(X,DX12)`      | literal-field branch below, store `0x4c033831`                 |
| 9, other effective field  | `(B * Q(Y,IY)) * Q(X,DXother)`     | alternate literal-field branch, store `0x4c033831`             |

### Effective standard field, without assuming an enum mapping

At `0x4c033733`, the generator reads model runtime pointer `+0xae8`
When nonnull, that pointer supplies the effective detail definitions
Otherwise it reads model `+0xae0`
The checks at `0x4c033749` and `0x4c03375b` compare the selected object's dword
at `+0x10` with literal integers two and one
Either match takes the `DY12/DX12` branch; all other values take the alternate
branch
No named drafting-standard enum mapping is needed or asserted here

The existing fresh model constructor `0x4c00edb0` initializes runtime `+0xae8`
to null in the private `cfg_ctormodel.c` model-constructor listing
The active model wire grammar embeds generated `moDetailDefs_c` at `fae0`
It does not contain a model-level `fae8` field
Current `builders/Styles.py::detail_definitions` rejects `standard != 1` and
writes `f10=standard` directly into the generated detail-definition fields
Thus this fresh construction's serialized detail field is literally one,
independently of any upstream enum's name
Its canonical dimetric construction uses `DY12/DX12`
An independent later runtime override of `+0xae8` must be treated as another
input/lifecycle operation, not assumed absent for every possible model

## Matrix layout and wire transform

For `q=(x,y,z,w)`, `quatToMatrix` at `0x31f0fe00` computes these intermediate
doubles and rows in the following form:

```text
x2=x+x; y2=y+y; z2=z+z
xx=x*x2; xy=x*y2; xz=x*z2
yy=y*y2; yz=y*z2; zz=z*z2
wx=w*x2; wy=w*y2; wz=w*z2
row0=(1-(zz+yy), xy-wz, wy+xz)
row1=(wz+xy, 1-(zz+xx), yz-wx)
row2=(xz-wy, wx+yz, 1-(yy+xx))
```

The first row is passed to unit-vector constructor `0x31f19110` at
`0x31f0fef8`, the second at `0x31f0ff21` and the third at `0x31f0ff4b`
That constructor computes `s=(vx*vx+vy*vy)+vz*vz`
If `s<1e-17`, the result is zero; otherwise it multiplies each component by
`1/sqrt(s)`
Every canonical row uses the nonzero branch
This per-row normalization is part of the recovered operation sequence

`0x31f0ff65` passes those three vectors to matrix wrapper `0x31e26c10`, which
calls `0x31e26880`
The latter stores the first vector at matrix offsets `0/8/0x10`, the second
at `0x18/0x20/0x28`, and the third at `0x30/0x38/0x40`
These are consecutive rows
It computes the identity classification using the native axis comparison with
tolerance `1e-12`; this does not transpose or reorder stored coefficients

`mg_RestoreXform` at `0x31f23ed0` copies that matrix directly into transform
`+8`, copies the supplied null vector into translation `+0x58`, and writes
scale one to `+0x70`
Its constructor state has transform flags zero and no perspective extension
No inverse or transpose occurs between the quaternion rows and this transform

Matrix save `0x31e039b0` walks three groups of three consecutive doubles,
incrementing its source pointer by eight after every write
Transform save `0x31e03ce0` emits matrix presence, those nine doubles when
present, the three translation doubles, scale and flags
This proves the existing active compact transform schema's field order:

| Active transform field     | Rule for these canonical views                                                        |
| -------------------------- | ------------------------------------------------------------------------------------- |
| `has_matrix`               | Zero for identity views 0 and 1 and every `f370`; one for canonical views 2 through 9 |
| `f08.m0..m8`, when present | The three normalized rows above, flattened in row order                               |
| `f58`, `f60`, `f68`        | Zero translation                                                                      |
| `f70`                      | Scale `1.0`                                                                           |
| `f78`                      | Zero flags; no `f80` extension                                                        |

The active provisional transform definition comes from `serial/defs/Definition.py`
Do not substitute alternate provisional offset keys from later registry modules

The quaternion/matrix layout and compound-view call order are **confirmed
static**
Floating-point library implementation differences can change final low bits
when another platform evaluates sine and cosine
This record therefore does not claim generated/native byte identity or native
viewport acceptance from the formulas alone
It does establish a generative computation rather than a saved matrix table

## Remaining acceptance and uncertainty

- Implement the shared default-view construction from the typed fields and
  operation sequence, with no runtime vendor DLL or resource-file dependency
  Canonical English resource names and documented binary constants are format
  vocabulary; the writer must compute matrices rather than load captured ones
- Verify the effective standard-field branch against the actual generated
  detail-definition input; require explicit rules before supporting runtime
  overrides or the nonzero base-orientation flag
- Measure generated named standard views in the native application, including
  isometric index seven, with healthy controls and unchanged geometry inputs
  Record returned view/camera orientation and screenshots rather than relying
  on the API call's lack of an exception
- Check whether the initial active viewport additionally depends on definition
  or UI camera state; this proof only supplies the model's canonical view targets
- Confirm body count, mass properties, feature edits and rebuild acceptance stay
  correct after adding the newly generated view objects and changed stream/map
  lengths

Only the oracle owner can establish those native outcomes

## Shared generator

`re/tooling/sw2026/builders/Views.py` implements the recorded operation sequence
and returns ten distinct view objects to the shared model constructor. Its
effective detail-standard input is explicitly limited to literal one, matching
the current detail-definition factory. Alternate branches remain recorded
knowledge, not exposed construction coverage. The complete-file process harness
checks the decoded view inventory, ids and matrix-payload presence. Remote CI
and fresh native geometry, edit and viewport measurements remain pending.
