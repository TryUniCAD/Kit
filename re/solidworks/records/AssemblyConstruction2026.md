# SOLIDWORKS 2026 fresh assembly construction

Fresh assembly generation and target-application acceptance are unproven. The source codec passes 14 exact stream round trips across two training assemblies, as recorded in [AssemblyArchive2026.md](AssemblyArchive2026.md). That result establishes exercised encoding. It does not supply fresh object values, native loadability, a solved mate graph, or usable component geometry.

## Authority and evidence

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) and the complete reverse-engineering playbook apply. Their stopping conditions remain: “There are two acceptable stopping conditions. The first is success under every criterion on this page. The second is the end of the available context. Missing grammar is the work. It is not a blocker.” The full parent goal continues.

This finding uses static metadata, constructor dataflow, exported accessors, and caller structure from the installed 2026 binaries. No execution trace or target-application measurement was collected by this component. Decompiled listings and analysis databases remain outside repository checkouts. No saved control supplied a constructor value or a default table.

| Module        | SHA-256                                                            |
| ------------- | ------------------------------------------------------------------ |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldmfcu.dll` | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` |

## Concrete class ownership

The runtime descriptor's schema is the u32 member at `+0x0c`; its object factory is the pointer at `+0x10`. The listed concrete classes have native schema `0x80000001`, whose wire schema is 1. The listed abstract bases have schema `0xffff` and a null factory. A source-code base serializer does not authorize emitting that base as a standalone object.

| Class                       | Runtime descriptor | Native object factory | Construction use                                                               |
| --------------------------- | ------------------ | --------------------- | ------------------------------------------------------------------------------ |
| `moAssembly_c`              | `0x4daca930`       | `0x4b655070`          | Concrete model root                                                            |
| `moChainComponent_c`        | `0x4daf0fa8`       | `0x4c20e710`          | Concrete chain component; self ownership still requires its initializer caller |
| `moContextChainComponent_c` | `0x4daf0fd8`       | `0x4c20e750`          | Concrete contextual chain component                                            |
| `moReferenceChain_c`        | `0x4dac9cd0`       | `0x4b653db0`          | Concrete reference path                                                        |
| `moReference_c`             | `0x4daca450`       | `0x4b654a00`          | Concrete reference feature                                                     |
| `moReferenceInternal_c`     | `0x4daca840`       | `0x4b654f40`          | Concrete internal-reference feature                                            |
| `moReferenceModel_c`        | `0x4dac8680`       | `0x4b651c60`          | Concrete model-reference feature                                               |
| `moConfigObject_c`          | `0x4daf1728`       | `0x4c20f510`          | Concrete per-configuration component state                                     |
| `moConfiguration_c`         | `0x4daf1968`       | `0x4c20f820`          | Concrete assembly configuration                                                |
| `moUnitComponent_c`         | `0x4daf1c98`       | `0x4c20fc70`          | Concrete unit component; the existing proven composition belongs to parts      |
| `moMateGroup_c`             | `0x4dac8d70`       | `0x4b6527c0`          | Concrete mate group                                                            |
| `moMateCoincident`          | `0x4dac9c40`       | `0x4b653d20`          | Concrete coincident mate                                                       |
| `moMateDistanceDim_c`       | `0x4dac9d60`       | `0x4b653e50`          | Concrete distance-dimension mate                                               |
| `moComponent_c`             | `0x4d130a58`       | null                  | Abstract base only                                                             |
| `moReferenceBrowser_c`      | `0x4cf7a840`       | null                  | Abstract base only                                                             |
| `moMateParent`              | `0x4ce481a8`       | null                  | Abstract base only                                                             |
| `moMate`                    | `0x4ce484e0`       | null                  | Abstract base only                                                             |
| `moMateNGeoms_c`            | `0x4ce48878`       | null                  | Abstract base only                                                             |
| `moMate2Geoms_c`            | `0x4ce488a8`       | null                  | Abstract base only                                                             |

These are native type facts, independent of document surveys. The [concrete-component gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/AssemblyConcreteComponents.md) records the construction consequence.

## Model root and subclass boundary

The concrete assembly factory `0x4b655070` allocates `0x1aa0` bytes and invokes protected constructor `0x4b67e710`. That constructor calls the shared model constructor `0x4c00edb0`. Raw instructions set `edx=1` at `0x4b67e75b`, clear `r8d`, then call the shared constructor at `0x4b67e760`. The part constructor `0x4c19e7b0` clears `r8d` and forwards its incoming `edx` at `0x4c19e7fc`. The argument's meaning is not inferred from this difference; shared-constructor dataflow remains the authority.

The shared model serializers are LW `0x4c22ec80` and RES `0x4c234150`. Fresh assembly composition must use those common fields and assembly-owned additions. A completed part graph contains incompatible subclass fields: assembly member `+0x14d8` is a string map, while the part member at that offset has a different wire owner. Calling the part builder and changing its class name is not a proven construction rule.

The common model-field factory is being extracted in the separately owned `Model.py` with explicit concrete node, self component, units, detail definitions, and relation graph inputs. The current proven part unit-component helper retains its part-only ownership guard.

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

| Owner/member                 | Classification                                         | Recovered construction rule                                                                                                    | Native evidence and unresolved boundary                                                                                                  |
| ---------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Model `f990`                 | Derived self component                                 | Must refer to a concrete component owned by the actual preallocated model node                                                 | Getter `0x4c0254c0` only returns this member; it is not a lazy factory. The assembly initializer that assigns it remains to be recovered |
| Chain component `owner`      | Derived owner reference                                | Parameterized construction takes the filed owner and its runtime header index                                                  | Constructor `0x4b8277f0`; the archive schema expresses the owner as the corresponding model object                                       |
| Chain component `f20`        | Derived reference path                                 | A supplied path is reused through its owner cache or cloned according to the constructor option and path state                 | `0x4b8277f0`, clone `0x4c28c490`; do not reuse a part unit-component record                                                              |
| Chain component `f30`        | Derived path bookkeeping, partial                      | Helper starts at 101 and adds virtual slot `0x16f8` from each linked path entry                                                | `0x4c291ca0`; concrete entry ownership and the virtual value's semantic role still require closure                                       |
| Context chain `f40`          | Derived external context                               | Created from the referenced filed owner on the resolved-path branch, or for shrink-wrap ownership under its separate predicate | Constructor `0x4b827ab0`, helper `0x4be8bcd0`; full external-file construction remains unresolved                                        |
| Context chain `f48`          | Unresolved context state                               | Constructor seed 0                                                                                                             | `0x4b827ab0`; seed is not an authored enum mapping                                                                                       |
| Reference-chain `f08`        | Derived path records                                   | Allocate a typed empty `moExtFeatureList_c`, then populate actual semantic path entries                                        | Constructors `0x4c28c5d0`/`0x4c28c670`, list constructor `0x4bac8d60`                                                                    |
| Reference-chain `f24/f20`    | Derived state/bookkeeping, partial                     | New chain initializes both to 0; cross-context cloning can set `f24=1` and clears selected state bits                          | `0x4c28c490`; final saved counter and state domains remain unresolved                                                                    |
| Config object `f08`          | Authored options represented by a derived typed object | Construct or copy a `moConfig_c` object                                                                                        | Constructors `0x4b8a5230`/`0x4b8a5480`; raw option enums are not accepted as semantic defaults                                           |
| Config object `f10`          | Derived contextual component                           | A non-context component becomes a new context-chain object; an existing context component is copied                            | `0x4b8a5230`, virtual `0x1b0` predicate, context constructors `0x4b827ab0`/`0x4b827a10`                                                  |
| Config object `f28`          | Derived referenced configuration                       | Embedded typed configuration-name/id state                                                                                     | Constructor `0x4b8a5230`; child configuration resolution and external ownership remain to be traced                                      |
| Config object `f18/f20/f148` | Unresolved flags/state                                 | Constructor seeds `0x111`, 0, 0                                                                                                | `0x4b8a5230`; these values are not a fresh saved-component recipe                                                                        |
| Config object `f140/f170`    | Derived optional transforms                            | Initially null; placement and secondary-transform assignment require the insertion caller                                      | `0x4b8a5230`; no blanket copy of one matrix into multiple caches is justified                                                            |

Ordinary insertion `0x4b6a7df0` calls `addReference`, then `onAddReference`; it accepts a target model, authored transform, referenced configuration name, and insertion options. It can preserve an explicit requested id by advancing the actual header allocator until that id is reached. The insertion path is the next dataflow target for concrete reference construction, placement, and per-configuration state.

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

The unresolved work is concrete and active: assignment of the assembly self component and relation manager; ordinary component-reference creation; external file/header/configuration identity; actual placement propagation; complete per-configuration option domains; solver state and common mate data; geometric bounds and cache policy; and controlled native load/rebuild/edit acceptance with passing controls.

No fresh assembly builder or native acceptance is claimed by this finding. No local tests, builder imports, fixture reproductions, or CAD operations were run. The caller and loop conclusions are static evidence, not Tupni execution traces.
