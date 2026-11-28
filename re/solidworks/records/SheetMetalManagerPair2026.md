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
