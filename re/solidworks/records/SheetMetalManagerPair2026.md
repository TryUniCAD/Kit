# SOLIDWORKS 2026 SP04.1 sheet-metal manager pair

An independently authored native discovery file from build 34.4.1.1011 rebuilt as sheet metal but failed the declared world-Z bounds. Both stock controls passed. The part was saved while still owned by the capture process and became readable after that process exited. Its SHA-256 is `93aaa4de1b0bc19b5e14c7d20339ed281f39e9e5d220344f7db1efd58b4bc9b8` and its size is 55,956 bytes. The failed capture used `c6c80926e1666229844a02bdba38221557372b50` and produced a failure receipt with SHA-256 `c22c18ddd663257717fd50ecb7a1b706f0bbc0fbff96c403034b862af67e6ad6`. The discovery archive remains unqualified.

| Stream | Normalized size | SHA-256 | Observation |
| --- | ---: | --- | --- |
| Contents/Config-0 | 25,354 | `f637eabccaebef11cc53b6a9815ea54e4d8ff91d314828d82c348a6d032afb7e` | Exact replay. The only physical configuration has no direct master, no legacy rows and no modern rows in Config. It supplies map count 110. |
| Contents/CMgr | 2,280 | `6c1407a9a1cafcf48f3a3c297dc98512e35174bb8a2c039133bbcf5f15dd89d7` | One typed pair in the manager's f660 list at mode 1. Complete replay with the proposed serializer. |
| Contents/Config-0-ResolvedFeatures | 36,970 | `0c224f3acb42ba899b7d610fd3d7a3ff8bfa6cf8130d70741fda44fc5308b3b3` | Inherited prefix 110. Typed traversal stops at byte 2,203 on moCutListFolder_c under moSolidBodyFolder_c. |

The pinned compatibility reader `b87f3b12b72874f4289b627d56e3740da2ab725b` originally refused the configuration manager at byte 2,182. The separate SDK-only configuration reader stops earlier at `moLengthParameter_c` schema 1. The linked research path uses the compatibility configuration reader and the exact inherited map. It does not inject the manager mode.

Static analysis used the installed `sldmodu.dll` SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`. The `moSMAndFPFeatIdPair` runtime descriptor is at RVA `0x29ad718`, has size 24, and advertises `0x80000001`. Its factory at `0x10ccba0` binds vtable `0x1ff1da0` and defaults the three fields to −1. Virtual slot `0x28` selects `Serialize` at `0x10e8b40`. The store and load arms call the signed Windows-long archive operators in field order `+0x08`, `+0x0c` and `+0x10` without an internal version or presence branch. The ordinary typed pointer wrappers use the same descriptor at `0x10d1100` and `0x10d2800`.

The linked probe consumes all 2,280 CMgr bytes and re-emits them identically with that candidate. The observed class record spans bytes 2,157 through 2,193 inclusive, slot 19, schema 1, with payload `(101, 39, 48)`. The first field matches outer key 101. The other identifiers lack independent API correspondence. The later sheet-metal class name appears at byte 23,538 of the resolved stream. A name occurrence cannot establish its typed bytes or membership.

Use the [capture procedure](SheetMetalCapture2026.md) to obtain a qualified base contrast, an added flange contrast and changed body membership. Run the linked probe separately on the disclosed discoveries and keep the holdout under seal until rules are frozen. The next resolved class and any populated direct master still need native and archive corroboration.

## Cut-list records at the resolved boundary

The SP04.1 `sldmodu.dll` vtable dispatch for `moCutListFolder_c` schema 1 enters RVA `0x10e0fc0`. It calls `moSubWeldFolder_c` at `0x10e97a0`, then `moSubAtomFolder_c` at `0x10e9560` and `moAtomBodyFolder_c` at `0x10d4f70`. The last class calls the already modeled folder serializer and then the same scalar and pointer sequence used by the solid and surface folder readers. The sub-atom layer adds an object list, a signed field, a feature-reference wrapper and two signed fields. The sub-weld layer serializes an inline property list.

At model generation 19000 the cut-list layer adds the component-feature pointer at `+0x498`, signed fields at `+0x4a4` and `+0x4a0`, a byte at `+0x48c`, a plane reference at `+0x468`, doubles at `+0x470` through `+0x480`, and signed fields at `+0x4b0` and `+0x4b4`. Historical layouts fall outside this research decoder.

The sort-options class uses descriptor `0x29adc28`, vtable `0x1f0af08` and serializer `0x10e1320`. Its record is a signed field at `+0x08` followed by the inline `suObArray` at `+0x10`. The observed signed value is 1 and the observed array is empty. The field's meaning and nonempty options remain to be measured.

| Research record | Payload interval | SHA-256 | Map count |
| --- | --- | --- | --- |
| Cut-list folder, slot 143 | [2,203, 3,072) | `314c5b217d542bce9036e258938e0421818b530cfbc803615269b4660ac8172c` | 144 → 172 |
| Sort options, slot 173 | [3,233, 3,239) | `36c159d76b52e03e496363607c5940227f62f4e048df344b050159bc97bba3d7` | 174 → 174 |

Both provisional records re-emit byte for byte from their actual incoming map. The read and write retain identical inherited entries and agree on the resulting class and object roster. The reported full-stream replay remains incomplete. The next unresolved typed class is `moTemplateSheetMetal_c` at byte 9,508.

## Template and bounded bend allowance

The SP04.1 `sldsmmu.dll` template-sheet-metal descriptor is at RVA `0x7806b0`. Its concrete serializer at `0x53cd00` forwards to `moSheetMetal_c` at `0x53ae10`. The parent calls `moSheetMetalCommon_c` at `0x53aae0`, which consumes the existing body-feature layout, its embedded `+0x808` record and the trailing integer members. The embedded record reaches the inline bend allowance when its presence byte is set. The native writer and reader branch on a helper archive-context member at `+0x890` for extra pointers and three signed fields. In the matching sldmodu.dll, moModel_c::loadResolvedFeatures at RVA 0x448760 reads CMgr.f658 after checking the model and manager at 0x448953 and writes it into helper +0x890 at 0x44895c. That happens before feature-list serialization at 0x4489e9. The linked research reader derives the mode from the fully replayed typed manager and its part context.

The unqualified discovery reaches the present bend allowance at offset 11,558. Its three initial unsigned array counts and two signed matrix counts are zero. The candidate reuses the typed dimension pointers and inline string arrays. It refuses any nonempty matrix or scalar-array count. No meaning is assigned to the flags or other scalars.

With diagnostic context zero, the template fails at byte 14,817 on the display-dimension pointer. With diagnostic context one, the complete payload interval `[9508,18090)` re-emits exactly and retains all incoming map identities. Its 8,582-byte SHA-256 is `c64e24a395290e5faf0b1673b3f187ff140642c3b996770384e2b4efeb97225c`, and the resulting map count is 292. The next typed refusal is `moSMBaseFlange_c` at offset 18,112. The public research switch reports the full-stream refusal and exits 2 because resolved traversal remains incomplete. The production reader and writer remain outside this research result.

## Base flange, flat template and resolved per-body owner

The SP04.1 sheet-metal module places `moSMBaseFlange_c` behind descriptor `0x780fe0` and serializer `0x538660`. It shares the bend-group base with the flat pattern. This base calls the common sheet-metal serializer, emits an inline object array and then one unsigned field. The base flange adds its profile pointer and two termination lanes conditioned on its lane mode and termination code. Four fixed inline groups each record a count and, when populated, a sketch pointer followed by that number of entity handles. The component-sheet-metal link forwards through `moCompSMDataObjFeat_c` to the existing component-reference layout and appends a signed field at `+0xe8`.

The flat template serializer `0x53ccf0` forwards to `moFlatPattern_c` at `0x5316f0`. The current serializer extends the bend-group base with three inline object arrays, typed feature and topology links, a conditionally written string, and an inline 108-byte bounding box. It then visits the context-dependent field and its signed pair count. Raw embedded flat body payloads remain outside this research rule.

| Research record | Payload interval | SHA-256 | Resulting map count |
| --- | --- | --- | ---: |
| Base flange, slot 293 | [18,112, 20,289) | `064dd9c2775899b1748c2eb97f5c206fd6a16c57793e196b079b5e25e78db45a` | 305 |
| Flat-pattern template, slot 306 | [20,318, 23,524) | `09b52147defeb8a2f3ccd4bb291795126a175c17b213f77fa0630d2e058c85da` | 329 |

The two complete payloads re-emit exactly from the same incoming archive maps. The typed list `moPartConfiguration_c.SerializeMBSMDataObjects.fcd8` in ResolvedFeatures reads the separate modern record `moPerBodySheetMetalDataNew_c`. Its native constructor identifies the virtual member at `+0x30` as `suDWordArray`, whose serializer forwards to the ordinary typed DWORD-array implementation. The first item follows its typed `f18` link to the flat-pattern record. The currently unresolved child `moFoldUpDownSketchFolder_c` is reached through that record at offset 35,613. This shows the modern record's ownership in this save. The direct master remains absent from Config-0.

## Complete linked research replay on two base saves

The fold-up/down sketch folder follows the ordinary folder serializer with two typed transform objects at `f570` and `f578`. The SP04.1 sheet-metal module's folder serializer is at RVA `0x5328a0` and its two transform children dispatch to `0x5329f0` and `0x532770`. Both child payloads are empty for transforms, properties and byte records in this discovery. The research layout retains typed transform fields and refuses unresolved property and byte-array contents.

The original unqualified native discovery consumed all 36,970 resolved bytes, produced 22 roots, and closed its map at 420. Its one inline modern row key 101 occupies slot 330 and links to sheet-metal slot 332 and flat-pattern slot 365. The 13,404-byte modern payload spans `[23566,36970)` with SHA-256 `cc457d78d230b3eb7fcacea5f03a72a7b676890ff67787cd159c1a81aaf338dc`.

An independently authored positive-Z A-only save on the thickness datum has archive SHA-256 `7deadafa95fd2960aabeefea4ad78f837914209b1cc0ac70761be5bd3b5ec3cb`. Its save receipt reports the intended `(0, 0, 0)` to `(41, 23, 1.25)` mm body and no errors or warnings. The same probe re-emits all 25,632 Config bytes, its 2,280 CMgr bytes and all 39,528 ResolvedFeatures bytes. The resolved SHA-256 is `be6eab77947b56f4fec14cfeab850fc925f203077a2c7098762cd5a004d1d5c9`. The part's 23 roots close the map at 434. One modern row with key 101 occupies slot 344 and links to sheet-metal slot 346 and flat-pattern slot 379. Its 13,404-byte payload spans `[26124,39528)` with SHA-256 `705c8979085900e416a7079ba7c3c4613cc8205bcd8d1ebb72d25ea28086fe39`.

In both records the first signed field is 101, matching the typed map key, and the second differs, 49 versus 51. The manager pairs are `(101, 39, 48)` and `(101, 41, 50)`. The remaining resolved integers and the empty DWORD array match. Association with independently measured native feature IDs, changes in body membership and nonempty contents still require the prepared contrast batch. Neither Config contains the direct sheet-metal master. The positive-Z save's batch failed to observe normal author and post-control process exits and never reached a fresh reopen. Its complete research replay does not qualify the native file or a writer.

The separate read-only reopen used the exact positive-Z archive digest and independent healthy stock processes. Its native source revision is 9f2f570a1e83e93fd6b1e9df5c8fdd85c799b498. The reopen reported the same `Base-A` bounds, volume 1.17875e-6 cubic metres, no load errors or warnings and a successful rebuild. `Sheet-Metal1` and `Base-A` were active. `Flat-Pattern1` was suppressed. Both stock controls read one body at 8e-6 cubic metres. Read-only reopen and both stock processes exited normally. The capture receipt SHA-256 is 334c7d1a643a37d0e6113065b2202769e9dfedf57798e45f8367c06d90d2d6ee. These receipts qualify the read-only observation of this one discovery. The original author exit and the wider batch remain unfinished.

The independently authored retained ca337256 A-only archive has SHA-256 784b8da6f1d1d9dcfee2ad2de2221995ca6f26fca9e39800e65819863a74088b. The frozen probe reproduces its complete Config, CMgr and ResolvedFeatures. The saved native feature IDs are 41 for Sheet-Metal1, 51 for Base-A and 50 for Flat-Pattern1. They match the two CMgr pair members and the base ID in the typed modern row in this exact archive. The first signed value 101 matches the outer row key. Native configuration ID and changes in those relationships under multiple bodies remain to be independently measured. Both stock controls passed, while the authoring process missed normal exit and the batch remained unqualified.
