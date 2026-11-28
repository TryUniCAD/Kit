# Environment insertion and cold part dirty propagation, 2026

The disclosed generated prism still opens with warning 32 and zero public bodies. The first measured part mask-1 transition comes from inserting a concrete ambient light into its environment folder.

## Exact ownership

The original pinned `sldmodu.dll` has preferred base `0x4b140000` and SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Complete function bounds, hashes, original RTTI, actual virtual cells and selected imports are in [the numeric record](PartEnvironmentDirtyPropagation2026.json). No proprietary bytes or listing is included.

The measured return chain is `moFeature::setNeedsUpdate` return `0x4bb516e5`, `moConcept::addFeature` return `0x4bda6384`, then environment insertion wrapper return `0x4b493612`. Feature ID 9 is the receiving environment folder. Member ID 27 and its vtable `0x4cda45d0` independently resolve by original RTTI to `moAmbientLight_c`. The insertion requests update 1 and name registration 0.

`moConcept::addFeature`, complete `[0x4bda62a0,0x4bda6446)`, inserts the actual child and, only when its fifth argument is nonzero, requests receiver virtual `+0xb8` with state 11, flags 0 and the actual added child as notifier. The environment folder uses the real feature setter, which propagates this nonzero state to its actual owner. The part model setter tail-jumps the node setter and produces the measured part `f0c: 0 -> 1`.

The 75-byte wrapper `[0x4b4935f0,0x4b49363b)` forwards dirty and name arguments unchanged. Its subsequent child `+0xb8(0,1,null)` request reaches a three-byte return leaf. The owning part remains dirty.

## Independently proved reload branch

`uiModelDoc::iPostLoadModel` calls `moModel::createDefaultLights` at `0x49799fa2` and returns at `0x49799fa8`, after a six-byte import call. Its immediate gates are: document `isDrawingDoc` false, actual environment list nonnull, and `moModel::hasLights` false. The concrete part document's virtual `+0x1260` is independently joined through its original RTTI/vtable/import thunk to `isDrawingDoc`.

`hasLights`, complete `[0x4c028f60,0x4c028fb9)`, tests actual environment and list presence and signed positive count. It then traverses the existing list and accepts any actual member with virtual `+0x1ed0` true.

`createDefaultLights` obtains a session-environment vector under native lookup vocabulary `Default`, creates each requested light kind, copies actual attributes and registers it through environment `+0xfd0`. Type 1 constructs the ambient class. `addNewFeature` translates its fourth argument to the base insertion's dirty-enable argument and requests name registration 0. The selected default-light call passes 1. The actual session attribute vector is not a constant or a document-independent construction recipe.

The extended scoped stop samples the wrapper caller after verifying the preceding frames. It reads `NodeRSP+0x138` as `0x4bda6757`, `NodeRSP+0x2c8` as `0x4c019fb4`, and `NodeRSP+0x4e8` as `0x49799fa8`. Loaded-module hashes agree with both original PE images. This joins the actual post-load caller to the ambient insertion during the same measured dirty write. The generated probe reproduces warning 32 and zero exposed solids. Its two independent ordinary controls report zero errors, zero warnings and one body. [Extended native observation](../measurements/2026/PrismEnvironmentPostLoadNative01.json)

## Limits and next experiment

The positive `replaceBody` and body-ID observations took place in separate processes. The order of the first dirty write relative to body publication and the effect of a generated light on ordinary open remain to be measured. The generated and native `f2b8` difference remains unassigned.

A separately authored one-light graph isolates the reload check while preserving real ownership and serializer fields. Its independently chosen coefficients and colour define an explicit presentation for the experiment. Two same-path guarded pairs preserve the kernel partition, complete downstream cache, original geometry IDs and part and folder flags. Only the five typed graph and bookkeeping streams change.

Both generated prisms open with warning 32 when their environment is empty. Both authored-light variants open with zero warnings and the save flag clear. All four variants expose zero solids until an explicit rebuild, which yields one solid with the independently expected mass properties. Both ordinary bracketing controls pass. The native candidate filenames differ within each pair, with independent same-path byte comparisons performed before the native batch. [Authored ambient native measurement](../measurements/2026/PrismAuthoredAmbientNative01.json)

## Verification

The source replay checks original module identities, complete unwind groups, bounded instruction and data hashes, imports and virtual cells. The [source receipt](../measurements/2026/PartEnvironmentDirtyPropagationSource01.json) binds the earlier disclosed observations. The extended observation has its own receipt above.

REA independently verifies the two unchanged original PE images as COFF AMD64 at evidence `ev_dce068421fbd5576d2d720304f0a68a8019d0cd19d551e09922617c41adf388d` and `ev_1a88dc36e115ae40c8d5c336ca0f4a80ead5979bba954f504b43862fe6f7a97c`.
