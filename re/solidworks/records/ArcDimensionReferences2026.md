# SOLIDWORKS 2026 arc dimension constraint references

Status: **phase-B static research; no new-family native acceptance**

This record derives geometry constraint-reference changes and value-dimension
index registration for the retained local `sgSketch::makeRadDim` path
It owns neither radial presentation nor parameter lifetime
See [CurvedSketchConstruction2026.md](CurvedSketchConstruction2026.md) and
[RadialParameterLifecycle2026.md](RadialParameterLifecycle2026.md)

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
state the stopping conditions exactly:

> There are two acceptable stopping conditions.
> The first is success under every criterion on this page.
> The second is the end of the available context.

The complete [instruction book](../../Playbook/README.md),
[Loader analysis](../../Playbook/LoaderAnalysis.md) and
[Orchestration](../../Playbook/Orchestration.md) were read for this pass
The repository skill and no-donor/no-runtime standards remain active
Static field rules do not establish native acceptance

## Evidence identity and scope

All addresses are preferred virtual addresses in SOLIDWORKS 2026 SP05.2
`sldmodu.dll`, build `34.5.2.0604`, image base `0x4b140000`
Its independently rechecked SHA-256 is
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`

Read-only PE metadata and exact bounded LLVM disassembly are the evidence
Existing private exports serve only as location evidence
No shared REA or Ghidra session was opened or changed
No vendor listing, vendor binary or saved document value is reproduced here
No CAD process was launched, attached to, automated, swept or closed
The user's unsaved drawing is outside this investigation
No local test or repository module was executed

The retained operation bound is a valid ordinary local 2D circle/arc handle,
with block index `-1`, retained value dimension and no deletion of that
dimension during the creation sequence
The primary constructor-initialized, map-null case has no optional
entity-to-dimension map
Block-manager references, equations, external geometry, map rebuilds and later
dimension deletion require their own traced operations

## Distinct counters and identities

| Owner                         | Field                            | Meaning in this investigation                                                                             |
| ----------------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Geometry `sg2DEnt`            | Runtime `+0x20`, wire `f20`      | Geometry constraint-reference count changed by `addConstraintReference`                                   |
| Value dimension `Dimension_c` | Runtime `+0x20`, wire `refcount` | Separate dimension lifetime count; actual circle-dimension add/remove virtuals are no-ops                 |
| `sgEntHandle`                 | Own runtime `+0x0c`              | Constructor zero; not the local geometry count and not emitted by the ordinary handle serializer          |
| Block-manager record          | Returned record `+0x0c`          | Separate counter in the block route, outside this local bound                                             |
| Value-dimension array         | Actual zero-based element index  | Used by the display handle and optional entity-to-dimension map; not a persistent ID or archive reference |

## Retained creation and geometry count

`sgSketch::makeRadDim` at `0x4c4cb670` constructs the temporary circle dimension,
appends its value record, creates its display and then adds one geometry
constraint reference
The radius/diameter choice does not split this final reference operation

| Operation                         | Exact anchor                                                     | Derived effect                                                       |
| --------------------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------- |
| Construct temporary `sgCircleDim` | Call at `0x4c4cb777` to `0x4c40fec0`                             | Temporary owns the new dimension state before append                 |
| Append to sketch value-G1 array   | Array load at `0x4c4cb785`, call at `0x4c4cb789` to `0x4c49aea0` | Append a `0x1a0` value record and return its actual zero-based index |
| Preserve returned index           | `0x4c4cb78e`                                                     | Index is retained for display creation                               |
| Create radial display             | `0x4c4cb7b5`                                                     | Receives the returned index in `R8D`                                 |
| Add arc constraint reference      | `0x4c4cb7c0` to `0x4c5bd330`                                     | Exactly one increment on the original arc handle                     |

`sgEntHandle::addConstraintReference` first dispatches validity at
`0x4c5bd33c`
For a valid local handle with `+0x1c==-1`, it resolves the actual geometry
through virtual `+0x378` at `0x4c5bd3a5` and tail-calls the geometry increment
at `0x4c5bd3b3`
The actual arc vtable `0x4d1c5ae8` resolves that slot to `0x4c562f20`

The geometry increment at `0x4c3e1510` reads signed `+0x20`, uses previous+1
when the previous value is positive, otherwise stores 1 at `0x4c3e1523`
This is an operation rule, not a saved-file constant
The common entity constructor `0x4c3e1030` initializes `+0x20` to zero at
`0x4c3e1065`
Consequently one retained ordinary radial dimension on a fresh arc derives
geometry `f20=1`
With positive, non-overflowing prior count, each further traversal of this
same creation operation adds one
This result must not be assigned to dimension wire `refcount`

## Append and optional index registration

The append at `0x4c49aea0` transfers the value record, then resets only its
source temporary at `0x4c49af7c`
The stored record address is calculated from array data plus
`0x1a0 * (count-1)` at `0x4c49af81`–`0x4c49af8e`
The optional registration helper `0x4c414820` is called at `0x4c49af92`
Its index argument is the zero-extension of the low 16 bits of the actual
array index
The append still returns the full signed actual index

The registration helper reads the copied dimension's sketch at `+0x88`
Only a non-null sketch with non-null `sketch+0x558` reaches map insertion
`0x4ba987f0`
It does not allocate the map, assign a persistent dimension ID, or increment
the geometry count
The fresh sketch constructor zeros `+0x558` at `0x4c4960ae`
No map is allocated by these append/registration bodies
A separate operation would have to create one before the non-null map branch
could apply

The append temporarily clears its array callback context and function,
restores them at `0x4c49af9f`/`0x4c49afa6`, then notifies the array's first
virtual callback with the full actual index range
The fresh value-G1 array has context/function null at
`0x4c495737`/`0x4c49573b`
Its callback `0x4b937760` returns unless both are non-null
Thus these notifications do not add a geometry reference in the fresh case

### Optional map representation

The observed map insertion `0x4ba987f0` creates a descriptor holding a
dimension array-class pointer at `+0x08`, the u16-widened array index at `+0x10`,
and its own list-attachment count at `+0x14`
That last count is a third independent count, not `sg2DEnt.f20`
For an actual `sgCircleDim`, the first matching classification is
`sgValG1Dim::GetThisClass`, selected at `0x4ba9883d`
The descriptor therefore uses the `sgValG1Dim` array namespace, rather than
the most-derived circle-dimension class
The map's ordered handle-keyed dictionary is at `+0x08`
Each key's list contains dimension descriptors
Within one handle list, equal descriptor class pointer and array index are
deduplicated at `0x4ba98c7c`–`0x4ba98c8d`
Insertion appends at `0x4ba98c9a` and increments only the descriptor attachment
count at `0x4ba98ca0`

The actual circle-dimension vtable `0x4cf79588` binds virtual `+0x3e8` to
`0x4b27e150`, which returns exactly one, and virtual `+0x4a0` to `0x4b287130`,
which returns the dimension address plus `0x130`
Thus insertion visits only `h1`, the ordinary arc handle
The other embedded handle at `+0x158` is not a second registered geometry
reference for this actual class

The actual arc handle's type virtual returns 2 at `0x4b285dd0`
For local `+0x1c==-1`, the insertion's preparatory helper `0x4ba994c0`
calls `sgSketch::getBlock` at `0x4ba994dc`
The latter returns null for that block index and type other than 13
The helper immediately returns via `0x4ba99601`
Therefore its block-list creation/clone path does not mutate the ordinary
local arc case

Map key ordering at `0x4c5bcef0` compares, in order, the handle type returned
by virtual `+0x120`, signed entity-array index `+0x18`, sketch pointer
`+0x10` as an unsigned address, then signed block index `+0x1c`
Handle flags `+0x08` and own member `+0x0c` are not part of this ordering
The node key is copied at `0x4ba98c15`; the copy constructor `0x4c5bccf0`
copies the complete `0x28` handle, including its dynamic vtable
This copy does not call the geometry increment

Insertion returns without adding a descriptor when map `+0x20` is nonzero
The exported `setNeedsUpdate` at `0x4ba99c80` writes that member
The query path calls exported `update` at `0x4ba98db1` when it is nonzero
The update method clears it at `0x4ba99f1e` and dispatches array rebuilds,
including the value-G1 rebuild helper `0x4ba9c300` at `0x4ba99f25`
The complete specialized rebuild is outside the retained-append bound
No claim that a dirty map immediately receives an append notification is made

These operations establish a runtime index lookup structure, independent of
the geometry count

## Lookup without the optional map

`sgEntHandle::getConstraints` at `0x4c5c41b0` uses the optional map when
`sketch+0x558` is present
Its no-map exact `sgValG1Dim` route instead scans the value-G1 array in
`0x1a0` strides
For each entry it obtains the first geometry handle through dimension virtual
`+0x4a0`, compares that handle with the queried geometry at `0x4c5c42df`,
and, after the observed skip predicates, returns the actual loop index through
the output index array at `0x4c5c4320`
It increments the result count at `0x4c5c4326`
No geometry count increment occurs in this scan

The observed skip predicates include nonzero dimension `+0x94` and a
conditional virtual `+0xc0` gate when global `0x4db93400` is nonzero
The latter is actual `sgDim::isDriven`, `0x4b28d760`, which returns whether
dimension word `+0x68` is nonzero
The semantics of the nonzero `+0x94` skip and global switch are not broadened
beyond these exact predicates
The initial `isTrimmed` gate at `0x4c5d0570` returns one immediately for
local block index `-1`; it does not exclude this bounded local case

For the same ordinary arc class, equality at `0x4c5bce10` requires equal
entity index `+0x18`, sketch pointer `+0x10`, block index `+0x1c` and matching
runtime class
The method has a separate cross-class compatibility branch which this record
does not generalize
Thus a local constraint reference can be found from the owning sketch's
value array and `h1` identity, without a per-arc index-list payload

### Lookup with a clean optional map

The map query `0x4ba98d70` expands only type-13 block handles
Its helper `0x4ba999d0` appends the original handle unchanged for ordinary
type-2 arc input at `0x4ba99ab7`–`0x4ba99abd`
The query then finds that handle's descriptor list in the ordered map

Each descriptor resolves back to its value array through `0x4ba997a0`
The `sgValG1Dim` route is array-data plus `0x1a0 * descriptor.index` at
`0x4ba997d5`–`0x4ba997e3`
The query skips nonzero resolved-dimension `+0x94`, then requires the
descriptor class namespace to equal the requested class at `0x4ba98f09`
It skips a driven dimension only when its separate observed global switch
`0x4db6d2f4` is nonzero
This is not the same global address as the no-map scan's switch
Accepted descriptor indices are returned at `0x4ba98f4f`–`0x4ba98f59`
The query increments its result count at `0x4ba98fff`

Neither a returned count nor a descriptor attachment count is automatically
equal to entity `f20`
Lookup applies filters, while geometry reference mutation is a separate
operation

## Serialized field boundary

The common entity serializer `0x4c583460` writes runtime entity `+0x20` as
a signed 32-bit field through the read at `0x4c5837a4` and archive operation
at `0x4c5837aa`
Its load branch reads the signed 32-bit field at `0x4c583d07` and assigns
entity `+0x20` at `0x4c583d10`
These are the active grammar's `sg2DEnt.f20` operations
The wire field is not the optional map descriptor attachment count

The neighboring entity pointer at `+0x28` is also independently identified:
the store calls the `moGroup` pointer writer at `0x4c583c55`, and the load
calls its pointer reader at `0x4c583f4b`
It must not be repurposed as a geometry constraint-index collection
The common entity grammar has the scalar count and this group field, rather
than a per-entity constraint-index list
This does not classify every other stream in the document

## Source reset, temporary destruction and display detach

The source reset `0x4c822050` clears source parameter `+0x28` and source
dimension lifetime counter `+0x20` among other base-dimension members
It does not reset the copied value-array entry or the arc entity count
It does not change the embedded geometry handles at `+0x130`/`+0x158`

| Source-only reset member                                    | Assigned value |
| ----------------------------------------------------------- | -------------- |
| `+0x50`                                                     | Signed `-1`    |
| `+0x08`                                                     | Signed `-2`    |
| Qwords `+0x18`, `+0x28`, `+0x40`, `+0x48`, `+0x54`, `+0x78` | Zero           |
| Dwords `+0x20`, `+0x30`                                     | Zero           |

After adding the geometry reference, `makeRadDim` destroys its temporary
handles and then its base dimension
The ordinary entity-handle destructor `0x4c5bcdc0` destroys only its optional
handle-owned data; it does not invoke `removeConstraintReference`
The base `sgDim` destructor `0x4c411dc0` forwards to the dimension destructor
The source parameter pointer has already transferred through the copy/reset
sequence
No geometry decrement is present in these temporary cleanup bodies

The separately traced display lifecycle in
[RadialParameterLifecycle2026.md](RadialParameterLifecycle2026.md) dispatches
actual `sgCircleDim` virtual `+0x1d0`/`+0x1d8` to the zero-return leaf
`0x4b27cbe0`
Its temporary display detach therefore preserves the geometry reference
It does not call the geometry `removeConstraintReference` merely because its
dimension remove-reference virtual was invoked

An explicit geometry remove-reference operation is different
`sgDim::iReleaseConstraintReference` at `0x4c428f80` calls the handle removal
for a non-null handle
The local route of `sgEntHandle::removeConstraintReference` resolves geometry
at `0x4c5d343e` and calls entity decrement `0x4c3e2540` at `0x4c5d3447`
That decrement skips deleted entities (`+0x54 & 1`), subtracts one from a
positive count, and invokes a zero-count callback through virtual `+0x178`
It is not an observed step of the bounded temporary cleanup
Later retained-dimension deletion is not proven by this record

## Operation-derived retained local rule

| Model operation                                                        | Required derived state for this bound                                                                                                                                                  |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Construct ordinary arc                                                 | Geometry count starts at zero from its common entity constructor                                                                                                                       |
| Append radial value dimension to a value-G1 array of length `n`        | New actual array index is `n`; length becomes `n+1`; the copied entry retains the arc as `h1`                                                                                          |
| Register through an existing clean optional map                        | Add `(sgValG1Dim namespace, n & 0xffff)` to that arc key's descriptor list unless already present; descriptor attachment count starts at zero and increases once on actual list append |
| Register with map absent                                               | No map object or per-arc list is created by this helper                                                                                                                                |
| Complete retained radius or diameter creation                          | Apply exactly one geometry reference increment after display creation; from fresh zero, entity `f20` becomes one                                                                       |
| Reset the append source and destroy temporary geometry/display handles | Preserve the copied value-array entry, its registered index and the geometry reference added by retained creation                                                                      |
| Query arc constraints                                                  | Recover array indices through the optional map or array scan and apply their exact skip predicates; do not write the query result count back into geometry `f20`                       |

This derivation is about the operation sequence and its typed owners
It supplies no saved value, stream span, offset patch or recorded field program

## Hash-bound evidence

Ranges are half-open preferred virtual address ranges and hashes cover bytes
read directly from the pinned external binary
Adjacent unwind fragments are combined only when the verified method control
flow joins them
Leaf ranges terminate after the verified return
No listing bytes or instruction program is reproduced

| Method or role                                    | Range                     | SHA-256                                                            |
| ------------------------------------------------- | ------------------------- | ------------------------------------------------------------------ |
| `sgSketch::makeRadDim`                            | `[0x4c4cb670,0x4c4cb882)` | `d927cd60080ad87d9b9e0108361f2b2b1727fa07335eb0b2d541175e3be70fde` |
| Circle-dimension constructor                      | `[0x4c40fec0,0x4c40ff03)` | `4752ad20c6751f99417d898d0865edd42adcdaca65fdc73503d651ed0cd7dc06` |
| Value-G1 append, three unwind fragments           | `[0x4c49aea0,0x4c49afc5)` | `a997c3fd9778efc49a6b9d54758ec5e19c6741feafb8cdb53c6a8011cf182bf3` |
| Fresh sketch constructor                          | `[0x4c495450,0x4c49645e)` | `5b351f5b063df2246cd9d98eba252efb5da24ba545d7fb8b2891af5e6b9cf8eb` |
| Common entity constructor                         | `[0x4c3e1030,0x4c3e121d)` | `980df4b8e792fc445db5624467a1e3eb3d82f0b629fe8a3663a16d2868fa75f3` |
| Handle add constraint reference                   | `[0x4c5bd330,0x4c5bd3be)` | `bf0ce32440df105202ad5214565cbb02c2361ae88258baf6f28e7ccd0441ca32` |
| Geometry increment leaf                           | `[0x4c3e1510,0x4c3e1527)` | `894830011c4110ef82424f820cf376eaf3f1094956b2e021cca45b9c2ca115ad` |
| Value-array callback leaf                         | `[0x4b937760,0x4b937779)` | `f84976947b2480191f1870c33d3ea745dbba5b074ec412b7dd4e0a0f176cdcbb` |
| Optional-map registration thunk                   | `[0x4c414820,0x4c414844)` | `2bc20696a719e7b32be9758497cbd5bad4c897da72cd44a28aaf2d3d4b8ebfc3` |
| Optional map descriptor insertion                 | `[0x4ba987f0,0x4ba98d3e)` | `bebbe43865eec016d549e5677d083b478d4deb5a28fa1b429f0032ef6648b8d3` |
| Actual circle geometry-count leaf                 | `[0x4b27e150,0x4b27e156)` | `2db31f4e09597946e56e859813bfdad7046d457c32332c3a882654d1e3ffdf67` |
| Actual circle geometry-array leaf                 | `[0x4b287130,0x4b287138)` | `c09d9193ba2cf3ebbbb4fa1440a6e20765c55ba70c6834d9ac175dd848450e86` |
| Actual circle driven predicate                    | `[0x4b28d760,0x4b28d76a)` | `597c39e2c960e931aa4445655b38e571791c8d76b2e7cb7fa8066a1fe23f00f3` |
| Actual arc handle type leaf                       | `[0x4b285dd0,0x4b285dd6)` | `7140f35dee6220b79b12aecc27acf5105bf3b77d1588e89fce345de7c16c72b7` |
| Actual arc geometry resolver                      | `[0x4c562f20,0x4c562f96)` | `7d2589239b66cd107ff43e5df124a0e9aa981ae79f2b5619d50128af2cd203ac` |
| Map insertion block-list preparation              | `[0x4ba994c0,0x4ba99617)` | `21fc70e551d2f014bbda0c613e0315f15dbf993622ab78f371f204589f93ff4c` |
| Sketch block resolver                             | `[0x4c4b0ef0,0x4c4b0f4d)` | `6777badc564b5b142516a61052dc6817904a64db483e168b8259f200e044ccb2` |
| Handle-key ordering                               | `[0x4c5bcef0,0x4c5bcf73)` | `ddf8987b8ceb7f2a54567263a13aa8ebabb55d99ba8e1d9aeab3d7a06a3fd6d8` |
| Handle-key equality                               | `[0x4c5bce10,0x4c5bced5)` | `902187ea2991d72170aeddd53e100ca636d089bba51f81edac5b0d1feae8ba36` |
| Entity-handle copy constructor                    | `[0x4c5bccf0,0x4c5bcd44)` | `3578feb698ec6d2c5b3cdd93c373cf501224852fa31156a1c4ce7edabd7849c3` |
| Handle constraint lookup                          | `[0x4c5c41b0,0x4c5c55fd)` | `2c8a65d7c7ce81bdf0bf199fad97ce5779aecc46b66915b8d3468f8d294d6928` |
| Initial lookup gate                               | `[0x4c5d0570,0x4c5d061f)` | `0562b978172a1a450adf6a26f4464b00996e7626c9dd20bb3e1336075abfce60` |
| Optional-map constraint query                     | `[0x4ba98d70,0x4ba99056)` | `b299127110febd85cb5e4177c5aace3be46759fdbdd46f807a28d34589ef2632` |
| Map descriptor-to-array resolution                | `[0x4ba997a0,0x4ba999c9)` | `598b45b1840699619dc4dd179a4863f115b6614f787d24275b4b302410ef94f9` |
| Map query handle expansion                        | `[0x4ba999d0,0x4ba99ad8)` | `d844208b1915811076e0177b5874ba07fada51700f50560feaf5c4b4012ae657` |
| Map update dispatcher, three unwind fragments     | `[0x4ba99e60,0x4ba99fc0)` | `abd05f81e8a59d4649761428d0a8d7a1c6a6ad07c12c69861c2a0e29bc84445f` |
| Common entity serializer                          | `[0x4c583460,0x4c5841ab)` | `b9695242d26f58ffd0eeaa1340a73291d4f8d9b92dd1b48daf55a885e8511375` |
| Source-only dimension reset leaf                  | `[0x4c822050,0x4c82207f)` | `7f27c4d16134dc15d80183e20a24970f3630fa90210afaa444518825fe51ac04` |
| Entity-handle destructor                          | `[0x4c5bcdc0,0x4c5bcdfc)` | `56ec16514744e7e05b07ed444234f479ac1c2aff06882f93a7c2d4738302cc31` |
| Base `sgDim` destructor                           | `[0x4c411dc0,0x4c411ddc)` | `3af16ac4c18e4615b13ac50463ab33d4db9ac4dd7f6e78f433ef98c6a3318dfc` |
| Handle remove constraint reference                | `[0x4c5d32d0,0x4c5d345c)` | `4d0f6dea2c9229c287f102cd5f4c834f0bf86674768a55c8bf452bd0895434be` |
| Explicit release-constraint thunk                 | `[0x4c428f80,0x4c428f8e)` | `01629822751dc093b1ca120c03c74db2715f73de2afa83a5025066d9c11bf70c` |
| Geometry decrement leaf                           | `[0x4c3e2540,0x4c3e2565)` | `de761002b69aa712d1bd546398848597557eadd0971f9c9add2e8554c532e719` |
| Display handle detach                             | `[0x4c845170,0x4c84520e)` | `6a380d26f51d3dd5afbdb8742360877f73c3f108c5f923b8429c26f9de38c416` |
| Actual circle-dimension add/remove-reference leaf | `[0x4b27cbe0,0x4b27cbe3)` | `4bc724f3b1d0caf4fe369c18cba3102e6c4ea057f63fe1587e3973134a7f755e` |

## Remaining gaps and acceptance boundary

The fresh retained creation count is **confirmed static and operation-derived**
The optional map descriptor, local insertion branch, ordinary query route and
the scalar entity serialization binding are **confirmed static**
The native code inspected has explicit u16 index truncation; this record does
not authorize support for actual value-G1 indices above 65535

The complete later retained-dimension deletion/compaction sequence, the
zero-count entity callback, specialized dirty-map rebuild `0x4ba9c300`,
cross-class handle matching and external/block geometry require separate
bounded traces before generalization
The wider meaning of dimension `+0x94` and the two query switches remains
unresolved; their exact skip behavior is recorded without choosing values for
them
No statement that entity `f20` equals filtered query length is established

No curve writer was implemented, no held-out native input was inspected for
writer work, and no native acceptance was claimed
The requested retained local operation is now bounded
The next acceptance action belongs to the oracle owner after the family input
lock; static findings here neither supply that lock nor establish native load,
rebuild, body, mass-property or editable-dimension success
