# AssetSettings observer indices

## Conclusion

The controlled dimensions' indices 4 and 5 are positions in a shared runtime observer list, not reserved dimension identifiers or a fixed constructor offset. The dimension constructor asks for an unindexed subscription; the native implementation appends at the current list length. The list starts empty. Entity observers and non-entity runtime observers enter the same list. Loading an entity's persisted subject record can change its stored index if another observer already occupies that position.

No additional persisted entities should be invented to explain missing positions. The exact identities or historical lifetimes of the two unrepresented positions in these controls are not established by static analysis. They can be non-entity subscriptions or unoccupied historical positions; claiming two particular runtime objects would exceed the evidence.

This refines the Design-only observation in the frozen [dimension model](DimensionModel.md). [ObserverSlots.json](ObserverSlots.json) now inventories all three saved entity segments. [ObserverNativeEvidence.json](ObserverNativeEvidence.json) records addresses, instructions, import-stub bindings, source hashes and thin-image hashes. [InspectObservers.py](InspectObservers.py) reproduces both inventories with the research decoder and static disassembler; it never executes production code or native Fusion functions.

## Persisted subscribers

| Archive | Design records | ACT records | Browser records | AssetSettings subscribers |
| --- | ---: | ---: | ---: | --- |
| Baseline | 256 | 9 | 34 | Browser2 DocumentSettingsBrowserEntry→0; Browser31 PMISettingsBrowserEntry→1 |
| WidthDimension | 262 | 9 | 34 | Same Browser subscribers; Design245 width dimension→4 |
| WidthDepthDimensions | 268 | 9 | 34 | Same Browser subscribers; Design245→4; Design255 depth dimension→5 |
| EditedDimensions | 268 | 9 | 34 | Same four subscribers and indices |
| Independently authored ProductionExtrusion | 172 | 8 | 33 | Browser202 DocumentSettingsBrowserEntry→0; Browser230 PMISettingsBrowserEntry→1 |

The native control's settings root is Design entity0. The independently authored accepted extrusion uses Design entity1000. Every inventoried segment fully decoded. Neither ACT nor another persisted Design/Browser entity contributes settings indices 2 or 3 in the controlled archives. Slots absent below the highest persisted index are evidence about the saved graph, not a serialized count of runtime objects.

## Static contract

All addresses below are unslid arm64 virtual addresses for Fusion2706.1.17.

| Routine | Evidence | Consequence |
| --- | --- | --- |
| `Ns::EntityObservers::EntityObservers`, NsDataModel10 `0x3309b4` | Zeroes list state, including count at object+8; initializes empty list sentinels | No reserved four-entry prefix |
| `Ns::Entity::subscribe(IEntityObserver*)`, `0x321e9c` | Sets index argument to -1 and branches to indexed overload | An ordinary subscription requests allocation |
| `Ns::Entity::subscribe(IEntityObserver*,int)`, `0x321714` | Adds to EntityObservers at `0x321948` before classifying the observer; Entity subjects are registered at `0x321bb8`, non-entity subjects through NonEntitySubjects_Debug at `0x321cdc` | Runtime and persisted observers share index allocation; only entity observers have persisted entity-subject frames |
| `Ns::EntityObservers::add`, `0x330e30` | Negative requested index branch stores current length at `0x331068`; nonnegative sparse index branch creates null callback entries | Allocation depends on current list state; a sparse requested index need not imply actual entities at lower positions |
| `Ns::Entity::addSubscribedObserver`, `0x321ea4` | At `0x322020`–`0x322050`, an occupied nonnegative requested index is replaced by -1 before insertion | Restore does not require the historical runtime occupancy to match |
| `Ns::EntitySubjects::postSegmentLoad`, `0x336544` | Reads subject index, resolves target, calls addSubscribedObserver, then writes the possibly changed index back at `0x3365e0` | Persisted index is a requested location repaired during loading |
| `Ns::EntityObservers::save`, `0x333400` | Asserts undo/redo/abort context before serializing observer vector; non-entity/null callback positions serialize false placeholders | The runtime observer vector is not an ordinary independently persisted entity list |
| `Ns::Dimension::Dimension::onPostCreation`, NsDimension10 `0x2081c` | Gets asset adapter settings, stores a settings PassiveRef, and calls the unindexed Entity::subscribe stub at `0x208b8` | No dimension-specific index4 constant |
| `SKs::SketchDimension::onPostCreation`, NaSketch10 `0x12c9e0` | Calls Dimension base at `0x12cacc`, then subscribes the dimension to each geometry using unindexed subscribe at `0x12cb2c` | Settings and endpoint subscriptions arise from two explicit constructor layers |

The literal4 at Dimension `0x2089c` and SketchDimension `0x12cad4` is an argument to `DataChange::test(ETransact,ETransact)`. It controls a creation/restore branch; it is not an observer index. Its enum name is not inferred here.

## Independent constructor proposal

A future qualified linear-dimension author can allocate a fresh, consistent observer namespace per observed entity. The current author already allocates Design observer subjects first and seeds Browser allocation with `ObserverCounts(Design.Records)`, which computes `max(existingIndex+1)` per Design target. With two fresh dimensions, settings indices0/1 can belong to width/depth and Browser indices2/3 to DocumentSettings/PMISettings. This is a proposed author ordering, not a claim that the controlled native document used that ordering. It requires native acceptance before production support is claimed. Retained archives should preserve their existing subject indices unless an explicit graph transformation reallocates all affected subscribers.

The dimension constructor must derive the complete graph already documented in DimensionModel: dimension plus Dimension continuation; named model parameter; DcDoubleParam plus ManagedEntity continuation; DynamicAttribute; settings and endpoint subject edges; model/user parameter expression binding; parameter-name lookup; parent/child collections; sketch dimensions; DcSketch parameter list; compute ordering and reciprocal dependencies. Width uses the ordered lower-left/lower-right point pair and horizontal constraint bit; depth uses upper-left/lower-left and vertical bit. These are separate from geometric constraints and anchoring. Parameter IDs, object identities, annotation positions and all collections remain explicit semantic inputs or derived outputs.

Subject indices are not substitutes for dependency edges. For a shared lower-left point, the two dimensions need distinct observer positions. Subject serialization order can differ from the dimension's geometry order. No fixed slots, synthetic baseline entities, captured records or source payloads are needed by this proposal.

## Verification boundary

Completed: read-only decoding of five complete three-segment archives; static inspection of 13 native code regions and exact imported symbol resolution. No local tests, production execution or native calls ran in this task. No production author or reader changed. Native creation, editing, regeneration and save/reopen of independently authored driving dimensions remain pending acceptance.
