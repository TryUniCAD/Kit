# Construction-plane visibility in a fresh part Definition

The document-wide `swDisplayPlanes` setting has a different owner from individual plane features and display states. A plain generated part uses `uiPartDoc_c.fad8_0` bit 17 for the authored Boolean. The 32-bit high word and all other bits keep their ordinary generated values. File offsets in the measurements describe each parsed graph layout.

## Exact loader build

The licensed 2026 SP04.1 `34.4.1.1011` binaries stayed outside the checkout. The `slduiu.dll` SHA-256 is `88a8d1bff1e8d7b5cad7e456096c4e32c8d84d4046fc5c09ce26f2563ee8e2a6`. REA PE inspection returned `ev_d5e8dda42dc70ccb84b65f3e25f39c5d842da8226fc4fe26968b2517d13f46cf`. The `sldprtu.dll` SHA-256 is `cb1e260f8411a39dc44f4d8a6255ea585c7a5e60b223d0e69d3f51a258ee96de`. The preferred-image addresses below identify independent x64 control-flow observations for those exact hashes.

| Owner | Observed path |
| --- | --- |
| Document API read | `slduiu` selector `5` in `iGetUserPreferenceToggle` uses branch `0x492a3200`, then `0x49949ca0` supplies `17` to live detail-mask slot `0x11c8`. |
| Document API write | The matching setter selects `0x492b3a84`, then `0x4994b830` uses the readback and calls slot `0x2840` for bit `17`. |
| Concrete part | RTTI identifies primary `uiPartDoc_c` vtable `0x334af0f0`. Its read and write slots import `uiModelDoc_c::getDetailMask` and `uiModelDoc_c::setDetailMask` respectively. The base methods at `0x497963a0` and `0x497c8100` use the bitset at `this+0xad8`. |
| Definition write | The model serializer at `0x49710220` copies the bitset from `this+0xad8`. It takes words `0` and `1` at `0x4971063e` and `0x4971065b`, then emits them through the archive scalar writer. |
| Definition read | The same serializer restores words `0` and `1` into `this+0xad8` through `utBitSet_c::setData` at `0x49711396` and `0x49711437`. |
| Optional override | A nonempty member at `this+0xae0` participates in a masked merge before writing. The mask at `0x4a64a560` includes bit `17`. This branch is outside the plain generated-part scope. |

The part serialization slot `0x1008` is at `0x333bb1b0`. The existing version-specific [Definition journal](../WriterResearch/DefinitionJournal.md) documents the derived-part routing into the base serializer. The surrounding native Definition graph has other presentation fields that remain governed by their own reader gates. [Optional override gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Presentation/DefinitionDisplayMaskCanUseAnOverride.md)

## Independent native source contrast

The [forward comparison](ComparisonProof.json) and [inverse source custody](InverseSourceProof.json) preserve separate captures. In the inverse batch, two warmed no-op saves shared one working path and produced byte-identical Definition streams. Both independent native getters read false before the setting and true after it. A fresh read-only open and rebuild retained true. Both stock controls passed and all five owned processes exited normally.

The inverse low word changed from `0x3fa48cfa` to `0x3fa68cfa` and the high word stayed `0x60001409`. The only Definition byte difference was at offset `186`, inside the parsed low word at `[184,188)`. Nineteen clear streams changed in the full native save. The strict Definition reader retains its alternate-renderer refusal on these originals. The independent capture establishes the selected setting and ownership for this scoped contrast.

## Replay the generated pair

Use the existing independently authored [plain geometry request](../measurements/2026/EncoderRoundTrip/Requests/BaselineReconstruction.json) in a complete trusted checkout. Wrap its decoded JSON object with `schema` equal to `kit.sw2026.document-construction-plane-visibility.v1`, `document` equal to that object and `show_construction_planes` equal to the selected JSON Boolean. Encode the whole request as sorted canonical UTF-8 JSON with a final newline, using `EncoderRoundTrip.Artifacts.canonical_json`.

```powershell
python -I -B re/solidworks/PlaneVisibility/ComposePlaneIntent.py --request $request --output $unusedOutput --native-locator $nativeLocator --written-at 1785626030
```

Reuse the recorded locator and epoch to match exact bytes. The [generated evidence](GeneratedPlaneProof.json) binds the fixture, candidate, recipe input and exact external access guard. Each variant is built from its complete persisted JSON by the ordinary typed part writer. The Boolean feeds `ModelDefInput.DisplayBits` before any stream is emitted. Invalid fields and invalid types fail before an output directory is created.

Strict SDK readback agreed across parameters, sketch, feature history and solid. Only `Contents/Definition` changed, with a single `00` to `02` byte at offset `114`, inside the same typed field at `[112,116)`. The generated pair remains research-scoped. Native validation and full source admission have separate evidence requirements.

## Native preflight and private recovery

The generated-pair preflight passed native open, rebuild and normal exit for two independent vendor controls. The system volume dropped from 100,474,880 to 55,001,088 free bytes. The process guard stopped before either generated candidate ran. All owned processes exited, and all input digests matched their original bytes. Generated native open, edit and reopen remain pending.

The immutable private recovery bundle is `D:/KitRuns/EncoderSwBossRea20261125/PlaneVisibilityLoader/PrivatePlaneEvidence01.tar.gz`. It retains the plane source plans and raw records, snapshots, request source bytes, exact generated archives and native preflight. The archived bytes agree with 75 original files and 12 source-request bindings. Its SHA-256 and private manifest SHA-256 are in [GeneratedPlaneProof.json](GeneratedPlaneProof.json). Verify those hashes before extracting to an unused private directory. Use the private manifest's original-path map to supply each exact request source and snapshot to the existing comparison tool. The sources and logs contain machine metadata and stay outside distribution. No originals were moved or changed.

## Verified native pair

The second native batch ran on the exact SP04.1 install after C: storage recovered. The original stopped preflight above remains immutable. Both generated archives opened read-only, rebuilt and remained unchanged. Both independent global getters matched the respective Off and On requests. Apart from those two booleans, the native Off and On observations agree exactly. Individual Front, Top and Right feature visibility values stayed `(1, 1, 1)`.

A private writable On copy completed the linked D1 edit, rebuild and SaveAs. The saved derivative was the exact input to a fresh read-only reopen and rebuild. Both getters stayed true and the saved `fad8_0` word was `0x00020000`. The stock controls and independently edited native reference passed. All seven owned processes exited normally. The two candidate artifacts and the derivative have separate digests. The reopened rebuild admitted one-ULP changes in centre-of-mass X, mass and volume through the existing independent geometry comparison. The exact SI D1 word matched before and after the reopen. [Revision-bound compact proof](NativeCandidateProof.json)

Use the verified private bundle `D:/KitRuns/EncoderSwBossRea20261125/PlaneVisibilityLoader/PrivatePlaneNative02.tar.gz`. Check its hash and its sibling JSON manifest hash from the compact proof, then verify every extracted member's length and hash into an unused private directory. The archive retains 41 members, including source bytes, requests, native records, derivative, exact runner and direct helpers. Four supplementary runtime helpers were hashed after the run from the exact clean Integration checkout. Keep those snapshots distinct from hashes in the terminal record. A licensed exact-build oracle and fresh owned sessions are required to repeat native measurements. The private evidence includes machine metadata and stays outside distribution.

This establishes vendor load and the observed native lifecycle for the disclosed generated pair on one build. The held-out geometry, alternate display overrides, full source preservation and public SDK qualification remain outside this result.
