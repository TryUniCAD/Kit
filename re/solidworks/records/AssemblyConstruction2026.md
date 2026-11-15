# SOLIDWORKS 2026 fresh assembly construction

Fresh assembly generation and target-application acceptance are unproven. The source codec passes 14 exact stream round trips across two training assemblies, as recorded in [AssemblyArchive2026.md](AssemblyArchive2026.md). That result establishes exercised encoding. It does not supply fresh object values, native loadability, a solved mate graph, or usable component geometry.

## Authority and evidence

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) and the complete reverse-engineering playbook apply. Their stopping conditions remain: “There are two acceptable stopping conditions. The first is success under every criterion on this page. The second is the end of the available context. Missing grammar is the work. It is not a blocker.” The full parent goal continues.

This finding uses static metadata, constructor dataflow, exported accessors, and caller structure from the installed 2026 binaries. No execution trace or target-application measurement was collected by this component. Decompiled listings and analysis databases remain outside repository checkouts. No saved control supplied a constructor value or a default table.

| Module        | SHA-256                                                            |
| ------------- | ------------------------------------------------------------------ |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldmfcu.dll` | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` |
| `sldmgu.dll`  | `99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c` |

## Concrete class ownership

The runtime descriptor's schema is the u32 member at `+0x0c`; its object factory is the pointer at `+0x10`. The listed concrete classes have native schema `0x80000001`, whose wire schema is 1. The listed abstract bases have schema `0xffff` and a null factory. A source-code base serializer does not authorize emitting that base as a standalone object.

| Class                       | Runtime descriptor | Native object factory | Construction use                                                |
| --------------------------- | ------------------ | --------------------- | --------------------------------------------------------------- |
| `moAssembly_c`              | `0x4daca930`       | `0x4b655070`          | Concrete model root                                             |
| `moChainComponent_c`        | `0x4daf0fa8`       | `0x4c20e710`          | Concrete component instance path                                |
| `moContextChainComponent_c` | `0x4daf0fd8`       | `0x4c20e750`          | Concrete contextual chain component                             |
| `moReferenceChain_c`        | `0x4dac9cd0`       | `0x4b653db0`          | Concrete reference path                                         |
| `moReference_c`             | `0x4daca450`       | `0x4b654a00`          | Concrete reference feature                                      |
| `moReferenceInternal_c`     | `0x4daca840`       | `0x4b654f40`          | Concrete internal-reference feature                             |
| `moReferenceModel_c`        | `0x4dac8680`       | `0x4b651c60`          | Concrete model-reference feature                                |
| `moConfigObject_c`          | `0x4daf1728`       | `0x4c20f510`          | Concrete per-configuration component state                      |
| `moConfiguration_c`         | `0x4daf1968`       | `0x4c20f820`          | Concrete assembly configuration                                 |
| `moUnitComponent_c`         | `0x4daf1c98`       | `0x4c20fc70`          | Concrete self component in named part and assembly construction |
| `moMateGroup_c`             | `0x4dac8d70`       | `0x4b6527c0`          | Concrete mate group                                             |
| `moMateCoincident`          | `0x4dac9c40`       | `0x4b653d20`          | Concrete coincident mate                                        |
| `moMateDistanceDim_c`       | `0x4dac9d60`       | `0x4b653e50`          | Concrete distance-dimension mate                                |
| `moComponent_c`             | `0x4d130a58`       | null                  | Abstract base only                                              |
| `moReferenceBrowser_c`      | `0x4cf7a840`       | null                  | Abstract base only                                              |
| `moMateParent`              | `0x4ce481a8`       | null                  | Abstract base only                                              |
| `moMate`                    | `0x4ce484e0`       | null                  | Abstract base only                                              |
| `moMateNGeoms_c`            | `0x4ce48878`       | null                  | Abstract base only                                              |
| `moMate2Geoms_c`            | `0x4ce488a8`       | null                  | Abstract base only                                              |

These are native type facts, independent of document surveys. The [concrete-component gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/AssemblyConcreteComponents.md) records the construction consequence.

## Model root and subclass boundary

The concrete assembly factory `0x4b655070` allocates `0x1aa0` bytes and invokes protected constructor `0x4b67e710`. That constructor calls the shared model constructor `0x4c00edb0`. Raw instructions set `edx=1` at `0x4b67e75b`, clear `r8d`, then call the shared constructor at `0x4b67e760`. The part constructor `0x4c19e7b0` clears `r8d` and forwards its incoming `edx` at `0x4c19e7fc`. The argument's meaning is not inferred from this difference; shared-constructor dataflow remains the authority.

The shared model serializers are LW `0x4c22ec80` and RES `0x4c234150`. Fresh assembly composition must use those common fields and assembly-owned additions. A completed part graph contains incompatible subclass fields: assembly member `+0x14d8` is a string map, while the part member at that offset has a different wire owner. Calling the part builder and changing its class name is not a proven construction rule.

The exported named assembly constructor `0x4b67efe0`, taking a document name, `su_CTime`, and an integer option, instead calls common constructor `0x4c00d8f0` at `0x4b67f037`. The corresponding named part constructor `0x4c19f170` calls that same common constructor at `0x4c19f1c7`; the named drawing constructor is another independent caller. This establishes its active construction role independently of an inferred Ghidra function signature.

The active common constructor creates `moRelMgr_c(owner=this)` and assigns `f9d0`. It also calls `moUnitComponent_c(model=this, filed_owner=this)` at `0x4c00e850` and assigns its result to `f990` at `0x4c00e85a`. Both allocations are on the common path. The default/runtime-factory constructor's null seeds therefore do not describe the completed named-construction owner graph.

The hypothesis that an assembly root should use a chain as its self component is **refuted before implementation**. Actual named assembly construction uses the unit component. Chain components describe instance paths. The common model-field factory is separately owned in `Model.py`, with explicit concrete node, self component, units, detail definitions, and relation graph inputs; the fresh composition must supply the active constructor's actual owner links.

The active constructor also assigns `moUnitsTable_c(1)` to user units at `f9b8`, while analysis units `f9c0` remain null at this stage. This is direct 2026 construction evidence, independent of the older-version loader branch. Explicit authored analysis-unit settings may require their separate creation path. The `suObList` pointer store at `sldmfcu.dll!0x3c8cceb0` passes the actual pointer to `WriteObject` without testing emptiness. Allocated empty active-constructor lists therefore cannot be equated to null on that store path. The common model factory's current null fields and native loader-created empty lists still need final graph-policy analysis.

## Assembly root field classification

Constructor seeds below describe initial allocation state. They are not universal saved-model constants or accepted neutral caches. Unknown semantics remain explicit and prevent claiming a complete fresh assembly profile.

| Field or group                  | Classification                               | Static rule or initial state                                                      | Evidence and remaining work                                                                                                                                      |
| ------------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `f14a0/f14d8`                   | Derived collections                          | Constructed empty string maps before authored assembly data exists                | Assembly constructor `0x4b67e710`; populate from actual semantic owners when those owners are recovered                                                          |
| `f1a18/f1a20`                   | Derived bounds/cache state                   | Both pointers are allocated bounding-box objects by the end of construction       | `0x4b67e710`; compute actual bounds or prove an accepted neutral state, rather than omit them because the pointers were briefly cleared                          |
| `f1560`                         | Derived counter, partial                     | Initial 0; browser-node insertion increments it once after reference construction | `0x4b6a7cf0`; ordinary insertion and deletion lifetime still need closure, so it is not equated to visible feature count                                         |
| `f1570`                         | Derived solver result, partial               | Initial 0; stored through the native solve-status enum                            | Getter `0x4b69e140`, setter `0x4b6b7950`; enum domain and completed solve state unresolved                                                                       |
| `f15a0`                         | Derived optional zone data                   | Initial null; native getter returns an object-array pointer                       | `getZoneArray` at `0x4b294eb0`; fresh absence requires the no-zone caller path                                                                                   |
| `f1608`                         | Derived optional mirror data                 | Initial null; native getter returns mirror-assembly data                          | `getMirrorAssemblyData` at `0x4b299510`; authored mirror instances need their own construction graph                                                             |
| `f18c8/f18e8`                   | Derived temporary collections                | Constructed empty object arrays for temporary fixed/grouped components            | Getters `0x4b2997d0`/`0x4b2997e0`; transient final-save treatment remains separate from initial allocation                                                       |
| `f1710/f1718/f1720/f1708/f1738` | Derived replacement graph                    | Initial flag 0, null objects, empty map; replacement type seed -1                 | Constructor `0x4b67e710`; `f1718` getter `0x4b299550`, type getter/setter `0x4b299730`/`0x4b29dba0`; no authored replacement operation may invent linked records |
| `f1940/f1948/f1990`             | Authored display option and derived lists    | X-ray toggle seed 0 and empty lists                                               | Getter/setter `0x4b298b80`/`0x4b29d900`; list population for enabled mode remains unresolved                                                                     |
| `f1674`                         | Authored plane selection, derived identifier | Initial -1; use the generated active-plane id when a plane is selected            | Getter/setter `0x4b298b50`/`0x4b29d8d0`; absent-plane semantics require the corresponding caller                                                                 |
| `f1a28`                         | Unresolved serialized state                  | Initial 1                                                                         | Constructor `0x4b67e710`; no semantic input or neutral-cache claim is made                                                                                       |
| `f1300`                         | Derived model update bookkeeping             | Assembly does not take the conditional increment branch                           | Primary vtable `0x4ce69b30`, slot `0x16d8`, points to `0x4b27cbe0`, exactly a false return; header counters are separate                                         |

The header update counter belongs to the actual header object. [ModelConstruction2026.md](ModelConstruction2026.md) records its independent increment and wall-clock timestamp rule. Neither header stamps nor assembly counters are derived from feature count alone.

## Components, paths, and configuration ownership

| Owner/member                 | Classification                                         | Recovered construction rule                                                                                                    | Native evidence and unresolved boundary                                                                                         |
| ---------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| Model `f990`                 | Derived self component                                 | Named construction supplies a unit component with the model as both target and filed owner                                     | Named caller `0x4b67efe0` reaches shared constructor `0x4c00d8f0`; assignment `0x4c00e85a`. Getter `0x4c0254c0` only returns it |
| Model `f9d0`                 | Derived relation ownership                             | Named construction supplies `moRelMgr_c(owner=this)`                                                                           | Shared constructor `0x4c00d8f0`; final save and authored relation population remain separate obligations                        |
| Chain component `owner`      | Derived owner reference                                | Parameterized construction takes the filed owner and its runtime header index                                                  | Constructor `0x4b8277f0`; the archive schema expresses the owner as the corresponding model object                              |
| Chain component `f20`        | Derived reference path                                 | A supplied path is reused through its owner cache or cloned according to the constructor option and path state                 | `0x4b8277f0`, clone `0x4c28c490`; do not reuse a part unit-component record                                                     |
| Chain component `f30`        | Derived path bookkeeping, partial                      | Helper starts at 101 and adds virtual slot `0x16f8` from each linked path entry                                                | `0x4c291ca0`; concrete entry ownership and the virtual value's semantic role still require closure                              |
| Context chain `f40`          | Derived external context                               | Created from the referenced filed owner on the resolved-path branch, or for shrink-wrap ownership under its separate predicate | Constructor `0x4b827ab0`, helper `0x4be8bcd0`; full external-file construction remains unresolved                               |
| Context chain `f48`          | Unresolved context state                               | Constructor seed 0                                                                                                             | `0x4b827ab0`; seed is not an authored enum mapping                                                                              |
| Reference-chain `f08`        | Derived path records                                   | Allocate a typed empty `moExtFeatureList_c`, then populate actual semantic path entries                                        | Constructors `0x4c28c5d0`/`0x4c28c670`, list constructor `0x4bac8d60`                                                           |
| Reference-chain `f24/f20`    | Derived state/bookkeeping, partial                     | New chain initializes both to 0; cross-context cloning can set `f24=1` and clears selected state bits                          | `0x4c28c490`; final saved counter and state domains remain unresolved                                                           |
| Config object `f08`          | Authored options represented by a derived typed object | Construct or copy a `moConfig_c` object                                                                                        | Constructors `0x4b8a5230`/`0x4b8a5480`; raw option enums are not accepted as semantic defaults                                  |
| Config object `f10`          | Derived contextual component                           | A non-context component becomes a new context-chain object; an existing context component is copied                            | `0x4b8a5230`, virtual `0x1b0` predicate, context constructors `0x4b827ab0`/`0x4b827a10`                                         |
| Config object `f28`          | Derived referenced configuration                       | Embedded typed configuration-name/id state                                                                                     | Constructor `0x4b8a5230`; child configuration resolution and external ownership remain to be traced                             |
| Config object `f18/f20/f148` | Unresolved flags/state                                 | Constructor seeds `0x111`, 0, 0                                                                                                | `0x4b8a5230`; these values are not a fresh saved-component recipe                                                               |
| Config object `f140/f170`    | Derived optional transforms                            | Initially null; placement and secondary-transform assignment require the insertion caller                                      | `0x4b8a5230`; no blanket copy of one matrix into multiple caches is justified                                                   |

The similarly named self-reference path is a separate runtime object. Assembly `makeSelfReference` at `0x4b6aa230` constructs `moReferenceEmbedded_c` with the model as both target and owner and stores it at `+0x1568`. The part method at `0x4c1b8530` stores its analogous object at `+0x1570`. Constructor `0x4bbb73e0` retains the target model at `+0x560`. Neither method assigns the serialized self component at `+0x990`; a newly constructed default transform in this runtime path is not evidence for a saved placement cache.

Ordinary insertion `0x4b6a7df0` calls `addReference`, then `onAddReference`; it accepts a target model, authored transform, referenced configuration name, and insertion options. It can preserve an explicit requested id by advancing the actual header allocator until that id is reached.

`addReference` at `0x4b6854d0` constructs a `moReference_c` through helper `0x4bbb7ba0` when its internal-reference option is zero. The nonzero branch invokes `0x4bbb74c0`, which uses the same helper and installs the `moReferenceInternal_c` vtables. With a nonnull authored transform, helper `0x4bbb7ba0` creates a copy at reference `f360` and increments `f3f0` from its constructor seed. This closes the reference's initial placement owner; it does not justify copying that matrix into every configuration transform cache.

`onAddReference` at `0x4b6ab9c0` reaches configuration insertion helper `0x4b8d4910`. That helper constructs a reference chain rooted in the reference's actual owning model, appends the concrete reference, constructs its chain component, and calls `moConfiguration_c::getOrAddObject` at `0x4b8d1400`. The configuration copies its selected `fc48` or `fc50` option record into a `moConfigObject_c`; selection depends on the concrete reference kind. The chain becomes contextual in that object's constructor. The actual configuration-name lookup supplies the referenced persistent configuration id. It then passes the name/id to config-object setter `0x4b8b2380` and reference setter `0x4bbcd7a0`. Header identity, external links, remaining option domains and context-dependent transforms are not replaced with captured values.

## Computed geometric bounds

The first implemented assembly construction operation is
`bounding_box(*, minimum: Sequence[float], maximum: Sequence[float]) -> dict` in
[`builders/Assembly.py`](../../tooling/sw2026/builders/Assembly.py). Inputs are
finite three-coordinate axis-aligned bounds in the model's length unit, with
`minimum[i] <= maximum[i]`. It returns the embedded `mgBBox_c.restore` field
mapping. Coordinates and derived state that exceed finite archive doubles fail
explicitly. This computes one record; it does not construct a usable assembly
or prove which owner cache should receive those bounds.

The following bounding-box constructor, serializer and getter addresses belong
to the hashed `sldmgu.dll` above.
`mgBBox_c::restore` at `0x31e02820` consumes ten doubles into members `+0x08`
through `+0x50`. Binary `save` at `0x31e03790` writes the same sequence. Getter
`high` at `0x31de5980` and getter `low` at `0x31de71b0` identify their respective
members. The point-pair constructor `0x31ddcf60` sorts each coordinate pair,
then computes the center and radius. Setter helper `0x31de85b0` computes the
same derived values from its low/high inputs. Its diagonal helper `0x31de3ee0`
explicitly squares the three differences, adds them and takes the square root.

| Wire fields | Native member       | Classification and formula                                                                          |
| ----------- | ------------------- | --------------------------------------------------------------------------------------------------- |
| `b0/b1/b2`  | `+0x08/+0x10/+0x18` | Derived sphere center: `(minimum[i] + maximum[i]) * 0.5`                                            |
| `b3/b4/b5`  | `+0x20/+0x28/+0x30` | Input-derived high corner: `maximum`                                                                |
| `b6/b7/b8`  | `+0x38/+0x40/+0x48` | Input-derived low corner: `minimum`                                                                 |
| `b9`        | `+0x50`             | Derived sphere radius: `sqrt(dx*dx + dy*dy + dz*dz) * 0.5`, where each difference is high minus low |

The default constructor at `0x31ddd2c0` instead creates center `(0,0,0)`, high
`(-1,-1,-1)`, low `(1,1,1)` and radius `-2`. Native `isSet` at `0x31de6ae0`
returns false when radius is negative or any high coordinate is below its low
coordinate. That invalid constructor seed is neither a computed geometric box
nor an accepted neutral cache. The builder deliberately requires actual bounds.
See the [bounds-state gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/BoundingBoxSphereState.md).

Insertion `sldmodu.dll!0x4b6ab9c0` updates assembly `f1a18` only after obtaining
both the reference box and current assembly box; it assigns the latter and
unions the former. The separate `f1a20` cache and final visibility/explosion
policy remain to be closed. Assembly `f1a28` feeds byte `+0x102` in the bounding
traversal context (`0x4b6c1ab0`); handler `0x4b6c9860` uses it to retain matching
user-component records even when their `hasBody` query is false. This closes a
specific dataflow use but does not yet establish the complete authored option.

The helper was statically parsed; no local builder import, serialization or
test execution was performed. Remote process coverage will exercise it with the
completed assembly graph rather than through a prohibited isolated unit test.

## Native configuration option profile

The `moConfig_c` runtime factory at `sldmfcu.dll!0x3c7c5ed0` invokes constructor `0x3c7c6010` with arguments `(2, 1, 1, 2, 0, 0)`. These are native constructor arguments, not values observed in a saved control. Their semantic enum domains are not all closed.

| Serialized member         | Role                                                                                     | Native initial rule                                    |
| ------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `f08/f0c/f10/f18/f20/f34` | Action, explode action, visibility, suppression, solving option, save-as-part preference | Copy the six constructor arguments                     |
| `f14/f28`                 | Exclusion and automatic suppression state                                                | Initialize 0                                           |
| `f38/f3c/f40`             | Display mode, hidden-line quality, shaded edges                                          | Initialize 6, 1, 0                                     |
| `f48/f50`                 | Display-state name/id pair                                                               | Helper `0x3c7c6110` constructs an empty name and id -1 |
| `f58/f5c/f60/f64`         | Tree hiding, suppression/visibility by pattern, zone-state flag                          | Initialize 0, 0, 0, -1                                 |
| `f68/f6c/f70/f74`         | Transparency, flexible-part, rigid-mass policy, SpeedPak hiding                          | Initialize 0                                           |

Getter bindings for those roles are recorded in [AssemblyArchive2026.md](AssemblyArchive2026.md). Fields `f1c/f24/f2c/f30/f78/f7c` are runtime-only in this version and are not added to the wire because their constructor initializes them. A fresh semantic option API still needs enum/domain and dependent-caller evidence.

## Remaining construction work

The unresolved work is concrete and active: complete ordinary component-reference construction; external file/header/configuration identity; context-dependent placement propagation; complete per-configuration option domains; solver state and common mate data; bounds-cache ownership and final visibility/explosion policy; and controlled native load/rebuild/edit acceptance with passing controls.

Only the geometric-bounds record constructor is implemented here. A complete fresh assembly builder and native acceptance are not claimed. No local tests, builder imports, fixture reproductions, or CAD operations were run. The caller and loop conclusions are static evidence, not Tupni execution traces.
