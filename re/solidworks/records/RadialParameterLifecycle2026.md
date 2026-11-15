# SOLIDWORKS 2026 radial parameter and reference lifecycle

Status: **phase-B static research; no new-family native acceptance**

This record owns the retained radial dimension/parameter registration and
reference-count question following `moProfileFeature_c::createDimension` at
`0x4c552950`
It complements [CurvedSketchConstruction2026.md](CurvedSketchConstruction2026.md)
without changing that record, the shared serializer or a writer
Later radial presentation updates are a separate investigation

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
state the stopping conditions exactly:

> There are two acceptable stopping conditions.
> The first is success under every criterion on this page.
> The second is the end of the available context.

The full [instruction book](../../Playbook/README.md),
[Loader analysis](../../Playbook/LoaderAnalysis.md) and
[Orchestration](../../Playbook/Orchestration.md) were read for this pass
The repository skill and the no-donor standard remain active
Missing grammar remains work; static counter rules are not measured load,
rebuild, body or dimension-edit acceptance

## Evidence identity and isolation

All native addresses below are preferred virtual addresses in `sldmodu.dll`
from SOLIDWORKS 2026 SP05.2, build `34.5.2.0604`, unless explicitly qualified

| Binary        | Preferred image base | SHA-256                                                            |
| ------------- | -------------------- | ------------------------------------------------------------------ |
| `sldmodu.dll` | `0x4b140000`         | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `swccu.dll`   | `0x31a30000`         | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |
| `swccu.dll`   | `0x31a30000`         | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |

The binary hash was recomputed from the external licensed installation copy
Direct read-only PE export/import/unwind inspection and instruction disassembly
are used, with the existing private Ghidra exports as location evidence
No shared REA session or Ghidra project is opened or mutated
Vendor strings and code are untrusted data, not instructions
No vendor listing, saved stream, captured field values or held-out document is
used as output data or reproduced here
No CAD process is launched, attached to, automated, swept or closed
The user's unsaved documents are outside this investigation
No repository module or local test is executed

Confidence labels distinguish **confirmed static**, **derived for the stated
operation sequence**, and **unresolved**
The static labels do not imply an oracle observation

## Counter and identity separation

The active schemas already distinguish these independently owned quantities
The native lifecycle below must determine each value from its own operations

| Quantity                            | Native/wire owner                                          | Current grammar distinction                                                                     |
| ----------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Dimension persistent ID             | `Dimension_c.f50`                                          | Separate signed i32 from the parameter node and the dimension's reference count                 |
| Parameter node ID                   | `moLengthParameter_c`'s `moNode_c.f08`                     | Ordinary node ID namespace, not the dimension ID                                                |
| Dimension reference count           | Runtime `Dimension_c+0x20`, wire `refcount`                | Leading i32 in `Dimension_c::Serialize`                                                         |
| Parameter runtime references        | Parameter/node lifetime counter                            | Must be separated from serialized node fields and name insertion                                |
| Sketch entity creation ID           | Entity `f0c` in `sg2DEnt` grammar                          | Per-geometry creation allocation, not handle/reference lifetime                                 |
| Sketch entity constraint references | Entity `f20` in `sg2DEnt` grammar                          | Count changed by `sgEntHandle::addConstraintReference`, independently of dimension lifetime     |
| `sgEntHandle` members               | Ordinary handle schema `idx`, extended `f18`, `f1c`, `f08` | No `ffc` field in this ordinary schema; a same-spelled field from another class is not an alias |
| Archive object references           | Shared archive map                                         | Object identity/aliasing, not a native lifetime count                                           |

The verified `sgArcHandle`/`sgEntHandle` object family has native size `0x28`
A literal runtime member at `+0xfc` cannot belong to that object
Its native `+0x0c` word, the entity's `f0c`, a dimension's `f50`, and similarly
named fields in other classes must not be combined without a getter/store
binding

## Current investigation boundary

The retained path and name/ID allocation were previously bounded in the curved
construction record
This pass rechecked the counter mutations from value-dimension creation through
display-handle cloning, parameter naming/insertion and temporary destruction
Values below are derived only for the explicitly bounded operation sequence
Counts for uninspected sharing, equation, external-reference or save/load fixup
paths remain unresolved

## Bounded retained operation sequence

The bound is an ordinary local 2D circle/arc, a private new length parameter,
null component and absent global-feature-reference/frozen-dimension cache,
with no equation relations, driven spline or pre-existing named dimensions
It uses the retained fresh-profile caller, rather than the separate caller
which names and then deletes a transient display
These conditions are necessary to use the rules below

| Step                      | Dataflow and native anchors                                                                                                                                                      | Consequence                                                                                                               |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Construct value dimension | `makeRadDim` at `0x4c4cb670` constructs `sgCircleDim` through `0x4c40fec0`; the common value-dimension constructor calls `createNewParameter` at `0x4c41177b`                    | A new length parameter belongs to the dimension; it is not an alias to a geometry scalar                                  |
| Append value dimension    | Value-array append `0x4c49aea0` copies the `0x1a0` value record, then calls source `Dimension_c::reset` at `0x4c49af7c`                                                          | Ownership of the parameter pointer transfers with the value record; the temporary's pointer is cleared before destruction |
| Resolve displayed value   | ValG1 display handles resolve their value-array index through actual virtual `+0x730`, target `0x4c8460f0`                                                                       | The display refers to the embedded sketch value dimension; it does not allocate a second parameter                        |
| Attach retained owner     | `moProfileFeature_c::createDimension` calls `makeRadDim` with null presentation-model argument at `0x4c55313e`/`0x4c553143`, then assigns the real profile owner at `0x4c553170` | Null presentation-model argument does not mean absent feature ownership                                                   |
| Name retained parameter   | The same caller obtains the display handle again at `0x4c55317a` and calls `nameParameter(handle,1)` at `0x4c55318b`                                                             | The display and its value dimension survive this naming path                                                              |

`setFeatureOwner` resolves the actual dimension at `0x4c84c29e` and stores the
profile pointer into dimension `+0x40` at `0x4c84c2b8`
The ordinary circle dimension's `+0x2c8` and the actual display handle's
`+0x468` resolve to zero-return target `0x4b27cbe0`, so neither the reference
dimension nor the extra owner-propagation branch executes
There is no assignment to handle `fe8` in this bounded owner operation

## Dimension counter: the actual radial overrides are no-ops

**Confirmed static:** the fresh `sgCircleDim` constructor installs vtable
`0x4cf79588` at `0x4c40fef7`, from the address formed at `0x4c40fef0`
Both its `+0x1d0` and `+0x1d8` entries target `0x4b27cbe0`
That target returns zero without reading or writing the object
The exported aliases at that shared address are not evidence of a different
class or a different implementation

The base implementations have different behavior:

| Implementation                             | Native rule                                                                                                                        |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| `Dimension_c` constructor `0x4c81f6d0`     | Stores zero into runtime `+0x20` at `0x4c81f6ff`; stores persistent-ID seed `-1` into `+0x50` at `0x4c81f717`                      |
| Base `addRef`, `0x4c8205e0`                | Increments runtime `+0x20`                                                                                                         |
| Base `removeRef`, `0x4c821850`             | Decrements runtime `+0x20`; its zero-count path releases the parameter through parameter virtual `+0x140` and the tolerance object |
| Actual `sgCircleDim` `+0x1d0` and `+0x1d8` | Both dispatch to the zero-return leaf; neither invokes the base increment/decrement                                                |

The following actual call sites preserve this distinction:

1. `moSkDimHandleValG1_c` constructor `0x4c83d4a0` resolves the actual embedded
   dimension and calls its virtual `+0x1d0` at `0x4c83d512`
   Its final constructor store at `0x4c83d520` installs actual handle vtable
   `0x4d242c18`; the address is formed at `0x4c83d519`
2. Actual handle virtual `+0x430` selects clone `0x4c83fae0`
   It allocates a handle and invokes copy helper `0x4c846460`
   The helper resolves the source dimension through virtual `+0x730` at
   `0x4c8464e4`, copies the handle, and calls that dimension's virtual
   `+0x1d0` at `0x4c8466ec` when its stated validity/cache/GFR guards permit
   The target remains the same no-op; copying a handle does not copy its
   private parameter or increment the parameter's node counter
3. In `sgArcHandle::createDispDim`, temporary-handle cleanup calls
   `iDetachDim` at `0x4c55f195` when temporary `+0xe8` is null, then calls
   `moDimHandle_c` destructor at `0x4c55f1a2`
   `iDetachDim` resolves the actual dimension and calls its virtual
   `+0x1d8` at `0x4c8451f7`; this is also the no-op
4. `moDimHandle_c` destructor `0x4c83da30` destroys optional handle-owned
   references/caches; it contains no direct call to the base dimension
   counter primitives
   The frozen dimension at handle `+0x100` is null in the stated fresh branch

The actual ValG1 handle vtable also binds `+0x730` to `0x4c8460f0` and
`+0x4b8` to `0x4c844ab0`
Its ordinary resolution path checks the value index and sketch lifetime, then
uses `getValG1ArrI` at `0x4c846192`; it returns the embedded dimension itself
The method spans three adjacent unwind records and ends at `0x4c8461ae`
Treating the first unwind fragment ending `0x4c846136` as the whole function
would omit the actual value-array resolution

**Derived for these operations:** dimension runtime `+0x20` remains zero
The feature-dimension rule relating reference count to constructed handle
count in [ProfileConstruction2026.md](ProfileConstruction2026.md) depends on
the feature dimension's actual base dispatch and must not be generalized to
`sgCircleDim`
Later presentation callbacks or other unexamined direct stores are outside
this bounded conclusion; the absence of a base increment is not a complete
whole-program write search

## Parameter lifetime, name storage and persistent IDs

`moLengthParameter_c` constructor `0x4c19bbe0` calls double-parameter
constructor `0x4c19baf0`, which calls `moNode_c` constructor `0x4c03c250`
The node constructor stores node ID `-1` at `+0x08`
Its eight-byte store at `0x4c03c27a` sets node flag word `+0x0c=1` and the
separate runtime lifetime counter `+0x10=0`
The subsequent parameter constructor's update initialization changes the node
flags; it does not turn `+0x0c` into the counter
The final length-parameter vtable is `0x4d123bf0`

| Parameter operation                             | Exact rule and ownership                                                                                                                                                                                                    |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Dimension_c::createNewParameter`, `0x4c820e10` | Creates the requested runtime-class instance, calls its virtual `+0x4d8` with null connection argument at `0x4c820e30`, then stores the parameter pointer into dimension `+0x28` at `0x4c820e37`                            |
| Actual length-parameter `+0x4d8`                | `moNode_c::connectTo`, `0x4b2fe0b0`; increments parameter runtime `+0x10`, without assigning node `+0x08`                                                                                                                   |
| Actual length-parameter `+0x4e0`                | `moNode_c::disconnectFrom`, `0x4c03dd80`; decrements parameter runtime `+0x10`                                                                                                                                              |
| Actual length-parameter `+0x140`                | `moNode_c::destroy`, `0x4c03dd40`; if a lifetime reference exists, invokes `+0x4e0`, then invokes the deleting destructor once `+0x10` is zero                                                                              |
| Value-array append                              | Source reset at `0x4c49af7c` clears temporary dimension `+0x28` and `+0x20`; the copied record retains the parameter pointer. The parameter is transferred, not connected for a second owner                                |
| Name storage                                    | `moParameter_c::setName`, `0x4c19c9b0`, calls `0x4b555250`. If parameter `+0x18` is null, the helper creates a `moNodeName_c` object and assigns its pointer at `0x4b5552ac`; otherwise it updates the existing name string |
| Parameter destruction from an actual dimension  | Base dimension destructor `0x4c81f790` calls parameter virtual `+0x140` at `0x4c81f820`, then clears its parameter pointer. This is separate from a display-handle no-op detach                                             |

**Derived for the private transferred parameter:** runtime node `+0x10=1`
through append, local display-handle construction/cloning, temporary-handle
cleanup and naming
Those operations do not create another parameter connection
An equation/shared-parameter branch can have other counts and is excluded

`nameParameter` calls the actual profile's virtual `+0x19d8` before choosing
a name
Fresh profile constructor `0x4c0ca780` installs primary vtable `0x4d0e8e80`
Its `+0x19d8` selects `0x4c0d6420`, which collects existing **display object
pointers** through `+0x1398`, target `0x4c0d7a70`
That method reaches `sgSketch::GetDims` at `0x4c499740`, which copies entries
from the existing display collection at sketch `+0x118`
It does not allocate parameters or allocate header IDs
The actual profile `+0x1ca0`, used for the additional name-object walk, selects
no-op `0x4b27e120`; that walk remains empty in this branch

The candidate integer begins at one at `0x4bea144b`
Ordinary `sgCircleDim` `+0x1e0` uses `Dimension_c::genParamName` at
`0x4c820f20`, whose prefix pointer `0x4db03700` supplies `D`
The current handle is skipped during name comparison at `0x4bea150f`
Thus the stated fresh empty-name case chooses `D1`
The general name-collision substring/case conventions remain unresolved

The chosen name passes from `0x4bea15e4` into handle `setName` at
`0x4c84c600`, then through actual dimension `+0x220` at `0x4c84c77a`
Circle `+0x220` selects sketch override `0x4c430bc0`, which calls common
`Dimension_c::setParameterName` at `0x4c430c20`
The common method first calls parameter `setName` at `0x4c821c67`
Only when dimension `+0x50==-1`, an owning non-viewer model exists and the
ordinary allocation mode applies does it call the model header's `getNewID`
at `0x4c821d0b` and store the result into **dimension `+0x50`** at
`0x4c821d11`
Repeated naming retains an already allocated dimension ID
None of this allocator dataflow writes parameter node `+0x08`

Consequently the dimension ID derives from the model header's shared allocator
at its actual allocation position, not the decimal suffix `1`, the display
list length or the value-array index
The parameter node ID retains its independent constructor seed `-1` for the
stated sequence
Name-object creation is name storage, not parameter-node ID registration
The earlier rename helper `0x4c84aec0` and sketch override's driven-spline walk
have no equation elements in the bounded graph; general equation registration
and the optional all-configuration rebuild marking remain separate work

## Ordinary 2026 store/load behavior

The active shared dimension definition is
`Dimension_c.Serialize` in `ResolvedDims.py`; it owns wire key `refcount`
`ResolvedSketch.py` has a provisional definition, but that is not a reason to
rename or merge its owner with `sgEntHandle`

**Confirmed static:** `Dimension_c::Serialize`, `0x4c8295c0`, reads runtime
dimension `+0x20` at `0x4c829655` and writes the leading i32 at `0x4c82965b`
It does not substitute the number of serialized display handles
The corresponding load at `0x4c829a0a` reads this wire i32 into a temporary;
`0x4c829a10` resets runtime dimension `+0x20` to zero rather than restoring the
read value
The inherited `sgDim::Serialize`, `0x4c5868d0`, calls this base at
`0x4c58692e`; it does not add a count fixup after the base

For ordinary modern file versions, base dimension load calls parameter pointer
helper `0x4c8349d0` at `0x4c829a44`, passing the address of dimension `+0x28`
The helper stores the parameter pointer through that destination at
`0x4c834a28` and calls parameter virtual `+0x4d8` at `0x4c834a35`
This rebuilds the parameter's runtime connection count
The superficially similar helper `0x4c821c10`, called at `0x4c829a83`, is
the older file-version branch below `0x21d`; it is not the active 2026 path
Its first argument is also a pointer to the destination parameter slot,
not a dimension or parameter object's base pointer

Actual length-parameter serializer `0x4c177fe0` calls common parameter
serializer `0x4c17a330` at `0x4c178004`, which calls `moNode_c::Serialize`
at `0x4c17a3ca`
For version at least `0xc7d`, that node method dispatches through actual
parameter `+0x4b8` and `+0x4c0` at `0x4c179d4c` and `0x4c179d5b`
The actual targets are `moNode_c::SerializeLWData`, `0x4c17adf0`, and no-op
`0x4b27e120`
The ordinary 2026 LW field order is name object `f18`, node flags `f0c`, node
mask `f28`, node ID `f08`, secondary mask `f2c`, and string `f20`
Parameter runtime `+0x10` is not a wire counter in this path
The called `swccu` `su_CObject::Serialize` at `0x31a3f030` emits no payload
when archive bit `0x10` is clear; its alternate DB/class-name path does not
serialize the parameter's `+0x10` or the entity-handle's `+0x0c`

There is one bounded indirect relationship between parameter lifetime count and
wire flags
Common parameter serializer `0x4c17a330` temporarily manages node mask bit
`0x20000000` around the call to `moNode_c::Serialize`:

- It preserves the original bit at `0x4c17a367`–`0x4c17a377`
- Under archive condition `3`, it sets the bit if already set or if parameter
  runtime `+0x10` exceeds `1 + (global[0x4db843e8] != 0)`; the counter comparison
  is at `0x4c17a395`
- Outside condition `3`, it temporarily clears a previously set bit
- It restores the original bit at `0x4c17a3dc`–`0x4c17a3ef`

The global's broader meaning is unclassified here
For the stated fresh private parameter count `1` with this bit initially clear,
the threshold cannot fire for either global value, so this mechanism introduces
no additional sharing bit
It must not be generalized to arbitrary shared/equation parameters

On load, common parameter serializer appends the parameter pointer to the
archive helper's object array at `+0x438` through `SetAtGrow` at
`0x4c17a4c4`, using that array's current count
This is archive-lifetime parameter registration, not header-ID allocation
It neither calls `connectTo` nor writes parameter node `+0x08`
The caller's later dimension-pointer helper supplies the runtime connection
described above

## Entity-handle ownership and misleading offset names

The ordinary `sgEntHandle` constructor `0x4c5bcd50` explicitly zeroes its own
runtime `+0x0c` at `0x4c5bcd91`
Its other members are flags `+0x08`, sketch pointer `+0x10`, entity index
`+0x18`, block index `+0x1c` and optional data pointer `+0x20`
That handle's own `+0x0c` has not been classified as a lifetime counter here
Its constructor zero is confirmed; its general semantic purpose is unresolved

The ordinary handle serializer `0x4c587800` emits the compact/extended entity
index, block index `f1c` and flags `f08`
It does not emit the handle's own `+0x0c` or its sketch pointer
Current wire keys are `idx`, conditional extended `f18`, `f1c`, and `f08`

`sgEntHandle::getConstraintReferenceCount` at `0x4c5c3d50` proves two distinct
owners:

| Branch                        | Counter actually read                                                                                                                                                                               |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Valid local entity, `f1c==-1` | Resolve the geometry through actual handle virtual `+0x378` at `0x4c5c3dbc`, then tail-call `0x4b282e20` at `0x4c5c3dca`. The leaf reads **entity** runtime `+0x20`, corresponding to `sg2DEnt.f20` |
| Block/data-manager route      | Obtain a manager record through `0x4c8f9bf0` at `0x4c5c3da3`, then read **that returned record's** `+0x0c` at `0x4c5c3dad`. The base register is the returned record, not the original handle       |

`addConstraintReference`, `0x4c5bd330`, uses the same ownership distinction
Its valid local branch resolves the entity at `0x4c5bd3a5` and tail-calls
entity increment `0x4c3e1510` at `0x4c5bd3b3`
Its block route increments the manager record's `+0x0c` at `0x4c5bd396`
The block route is outside the local radial construction bound

Therefore no `sgEntHandle.f0c` or `sgEntHandle.ffc` wire count should be invented
from the indirect `+0x0c` read
Nor may entity `f20` be substituted for dimension wire `refcount`
The label `ffc` does exist in unrelated active definitions, including
`sgParabola` and `sgLogG2Dim`; those fields have their own class owners,
types and serializers
The parameter's wire `f20` is a string, again unrelated to either numeric
runtime counter at the same offset in another class

## Hash-bound method extents

Ranges are half-open preferred virtual address ranges, hashed directly from
the pinned binary's mapped file data
Adjacent unwind fragments are combined only where the verified method control
flow reaches them
Leaf ranges without unwind metadata stop after the verified return
These are digests and independently recorded rules, not vendor listings

| Method or role                                            | Range                     | SHA-256                                                            |
| --------------------------------------------------------- | ------------------------- | ------------------------------------------------------------------ |
| Retained profile `createDimension`                        | `[0x4c552950,0x4c553e30)` | `23b377359d2456e7bc10043424e380311ad78ab9a401f4e2b7915c047b50b2d3` |
| Circle dimension constructor                              | `[0x4c40fec0,0x4c40ff03)` | `4752ad20c6751f99417d898d0865edd42adcdaca65fdc73503d651ed0cd7dc06` |
| Base dimension constructor                                | `[0x4c81f6d0,0x4c81f73e)` | `7c0995048f579ca61b0c8ca5e53f8c0253a16c3575ea416e3468a433a7913a00` |
| Create new parameter                                      | `[0x4c820e10,0x4c820e46)` | `071e21d7f23ee0be7a0a46f999fa422a32a6fd3a4af81bba451e03ff1e62da6f` |
| Value-array append, three unwind fragments                | `[0x4c49aea0,0x4c49afc5)` | `a997c3fd9778efc49a6b9d54758ec5e19c6741feafb8cdb53c6a8011cf182bf3` |
| ValG1 handle constructor                                  | `[0x4c83d4a0,0x4c83d536)` | `6a587b10909d215fa1b7f1616ca3bee0c1d1435c8e3ef8b83bfbcf08134e5f04` |
| Actual ValG1 dimension resolution, three unwind fragments | `[0x4c8460f0,0x4c8461ae)` | `babaf99b1ea9f17d8ee87ed1dbc46c4feb6f4edcc777bde0d7435cc9482eeea2` |
| Handle clone                                              | `[0x4c83fae0,0x4c83fb3d)` | `68f32dff10f40f734ee352b2327d9382e1796e0a41ba12193891d59a2c9daacb` |
| Handle copy helper                                        | `[0x4c846460,0x4c84696d)` | `acec981798cf2212358ef14e071a963a78294b545a6a57d0efba2453b7e43392` |
| Handle detach                                             | `[0x4c845170,0x4c84520e)` | `6a380d26f51d3dd5afbdb8742360877f73c3f108c5f923b8429c26f9de38c416` |
| Handle destructor                                         | `[0x4c83da30,0x4c83dbfc)` | `4936f706f73fa9341cc5dc25aec4746fc9553ef71c0434720e43e8db74d3fccf` |
| Zero-return virtual target                                | `[0x4b27cbe0,0x4b27cbe3)` | `4bc724f3b1d0caf4fe369c18cba3102e6c4ea057f63fe1587e3973134a7f755e` |
| No-op virtual target                                      | `[0x4b27e120,0x4b27e123)` | `b6cbececf1b07e74f37d57710c68c31f0b92cb08d51093252b321b07542e177b` |
| Owner assignment, five unwind fragments                   | `[0x4c84c280,0x4c84c3f1)` | `053f73584ab226b62c642dbd6f9dec066a8917b23acbf4d7074e428a4d87c363` |
| Feature name selection                                    | `[0x4bea1400,0x4bea1656)` | `f5dbacfc0dd7e4b5f3ab00dcc9f405b4a2418f0579718cc1c1822afe711539c7` |
| Common dimension parameter naming                         | `[0x4c821c40,0x4c821d69)` | `0e415a01819436714d3a891db3df28dc48fa5e99d3f7f110122343bb99f7d1dc` |
| Sketch dimension naming override                          | `[0x4c430bc0,0x4c430d81)` | `45af6eca1294f9034d5816c4396720e1dc80723549e493ac95f156392fcabc5b` |
| Parameter name setter                                     | `[0x4c19c9b0,0x4c19ca17)` | `a2b861de02ee0d3bb4e235a5d2257ca2b507e81558ac3ad2406ecb08c5b4c48b` |
| Node-name storage helper                                  | `[0x4b555250,0x4b5552da)` | `c39604d865d3fb8bf212aa1cd125b634bbe4e4feb30ddf7671131ba8b5a0ffd1` |
| Node constructor                                          | `[0x4c03c250,0x4c03c2b7)` | `162d31cd9a7dbdb25da3d81575df765fd763cb5b455d12af7250e3a9c2a7dfe4` |
| Node connection increment                                 | `[0x4b2fe0b0,0x4b2fe0b9)` | `cafce5c7d91568b889edaf162524541511f49c66f5cee849b498e1b5c9dcfd16` |
| Node connection decrement                                 | `[0x4c03dd80,0x4c03dd89)` | `c7a5a9d3fa5c48ab5b90a0dbb63c988edd648b7a5240acde8ca04a93e2259478` |
| Dimension serializer                                      | `[0x4c8295c0,0x4c829e3b)` | `13fbad6d49022d0b89560877b96e8dfdd3cda9855cdc04057115f1d5e8e7f60f` |
| Modern parameter pointer helper                           | `[0x4c8349d0,0x4c834a46)` | `208093f059a5c338360e406e731ac57536888349c96c5796effd2a8b868a502d` |
| Double/length parameter serializer                        | `[0x4c177fe0,0x4c178184)` | `3a3ee2166a7847e93efff0ff9306354dd0ce278b59903bee5b57e89d7666fa6c` |
| Common parameter serializer                               | `[0x4c17a330,0x4c17a665)` | `b5068e261959921bd7f4555328fdc131333d73e732b60dbd52ac6220b531264f` |
| Node serializer                                           | `[0x4c179cf0,0x4c17a322)` | `20ea9bfa3a3f3c3306a12f73a6b3452b27e057fd7788dae11647b1914037b744` |
| Node LW serializer                                        | `[0x4c17adf0,0x4c17b23a)` | `5f5262d0f62d2bbcea73730a56fc2b7ea8bf8489a066d84df4b9902536553760` |
| Entity-handle serializer                                  | `[0x4c587800,0x4c587bea)` | `e8dff64e197009294ec10465a92ec0efc40f696c9221b698cab534794250cfba` |
| Entity-handle constraint-count getter                     | `[0x4c5c3d50,0x4c5c3dd7)` | `7fe962eecaf71d9ddfe69dc5317d1ceff86681f6f5d5735bf0de939448725e3b` |
| Local entity `+0x20` getter                               | `[0x4b282e20,0x4b282e24)` | `07ad3a50b1c271e07fb57fb47d2f0e77f3342d41bfa410990cb1320a45035fb2` |
| `swccu` base object serializer                            | `[0x31a3f030,0x31a3f0c9)` | `d064fda3876f5279a158324ef2252caeee3765c0638ff7c2afb4dbc333b3db77` |

## Remaining evidence and acceptance boundary

The tracked fresh local lifecycle derives dimension counter zero, private
parameter runtime references one, independent parameter node ID `-1`, and a
dimension persistent ID allocated during actual retained naming
It does not derive a constant dimension ID or a count from the number of
archive references
The exact general name-collision conventions, shared/equation parameter
lifecycle, block data-manager serialization and meaning of the handle's own
runtime `+0x0c` remain unclassified
Broader parameter-node construction/insertion order relative to other model
nodes is not recovered by this caller trace; retaining a constructor seed in
this sequence does not establish a general ordering policy
Later radial presentation updates and any subsequent direct dimension-counter
stores must be accounted for before treating the tracked state as a final save

This pass added recorded knowledge only
It neither implemented a radial writer nor inspected a held-out native stream
There is no native load/rebuild/edit or measured body acceptance in this record
Native family locking and the isolated oracle owner's controls remain required
