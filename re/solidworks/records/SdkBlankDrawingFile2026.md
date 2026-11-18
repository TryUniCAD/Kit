# SDK-only blank drawing file construction in 2026

The internal SDK constructor now generates all seven streams and the enclosing native container for one ordinary unformatted blank drawing from genuine portable drawing semantics. This slice has offline process evidence only. It does not enable the public writer or establish new native or held-out acceptance.

## Ownership and boundary

Task: `PR121-SDK-DRAW-BLANK-FILE`. Owner: `configuration_header`, coordinated by the PR #121 root. Delivery: PR #121. Dependencies are the measured sheet/model constructors, shared Definition and header executors, the shared fresh history/self-file/framing helpers, and the current archive-19000 container writer. The slice exit condition is complete SDK-only construction, full typed readback, exact independent generated file parity, rejection of unsupported portable content, and a frozen reviewable source set.

`MakeBlankFile(BlankDrawInput)` consumes an actual `DrawingData`, explicit `DrawDocOptions`, `ModelDefSettings`, `HeaderInput`, `SelfFileInput`, and `HistoryInput`. The portable drawing supplies its sheet identity, name, paper dimensions, active sheet and ratio. Options supply native presentation, independent UUID4 and model naming. Header/history/file inputs supply explicit authoring and save provenance. No native document, captured field sequence, research object or runtime filesystem lookup supplies a field.

Admission is one active, view-free ANSI A landscape sheet, no linked models, positive integral scale terms from 1 through 999999, and the previously bounded style/unit/current-target profile. The constructor rejects unsupported sheet content, paper, ratios, invalid names, UUID domains, inconsistent creation provenance, bad save chronology and unsupported UI options. The research stdin mapper preserves explicit view/model-reference input and rejects unknown fields; it cannot discard unsupported content before the SDK guard sees it.

## Construction owners and field provenance

| Owner                                 | Inputs and rule                                                                                                                                                           | Prior source authority                                                                                                   |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `moDrawing_c` and sheet/support graph | Actual sheet intent, native presentation, allocator registrations and explicit UUID4                                                                                      | [Model factory](DrawingModelConstruction2026.md), [sheet factory](DrawingSheetConstruction2026.md)                       |
| `uiDrawingDoc_c`                      | Shared `MakeDefHead`/`MakeDefTail`, actual model and UI sheet-sketch aliases, drawing CLSID, drawing mode 2 and terminator `0x0daf`                                       | [Definition grammar](DrawingDefinitionGrammar2026.md), [shared model Definition](SdkModelDefinition2026.md)              |
| Drawing `moHeader_c`                  | Actual model/log owner, actual next persistent ID, explicit author/company/comment and epochs, initial update/body counters 101, no external directory and no part bounds | [Model construction](ModelConstruction2026.md), [drawing root](DrawingEmptyManagers2026.md)                              |
| Self `moExtObject_c`                  | Shared `MakeSelfFile`: actual model kind/name, explicit Windows destination and save epoch; drawing's empty configuration name and ID minus one                           | [Self-reference construction](AssemblyConstruction2026.md#ordinary-self-reference-construction)                          |
| Biography/history                     | Shared fresh typed owners and independent stream maps; authored provenance with the non-native-save branch                                                                | Shared `Archive/Construction/Metadata` and `Archive/History` rules; [history classification](HistoryConstruction2026.md) |
| Model stamps                          | Scalar encoding of the actual header creation/update/body members                                                                                                         | [Metadata construction](MetadataConstruction2026.md)                                                                     |
| `KeyWords`                            | Actual native sheet ID/name/ratio; immutable ordinary paper vocabulary; common `FrameKeywords` with drawing empty-tag spelling                                            | [Sheet indexes](DrawingEmptySheetConstruction2026.md), [property-prefix evidence](DrawingPropertyPrefix2026.md)          |
| SolidWorks information                | Six sheet-derived values, fresh IDs `3 + ordinal`, matching name dictionary, unqualified section/property records and explicit per-tree `vt` prefix                       | [Section grammar](DrawingPropertySections2026.md), [literal-prefix rule](DrawingPropertyPrefix2026.md)                   |
| Container                             | Existing SDK generative emitter, no template argument; directory, lengths and compression derive from the seven computed stream payloads                                  | Existing [container emitter](../../../src/convert/adapters/solidworks/Container/Container.py)                            |

The header and UI retain the actual newly constructed model objects. The self record retains the actual modeled name independently from its destination basename. The final persistent counter remains nine and the blank Definition map's next index is 131. The private bridge used by earlier model proofs is absent from this writer.

The property constructor uses literal namespace declarations on its own tree, without ElementTree's process-wide namespace registry. Property IDs and dictionary entries derive from ordered modeled values, with no captured native property rows. XML names/text are validated and escaped through the standard library. Unicode, quotes, angle brackets and ampersands survive the whole-file checks.

## Executable proof

`re/tooling/sw2026/DrawingSdkProcess.py` accepts the declared neutral stdin job, imports code before the guarded phase, then constructs the SDK file with no research builder/serializer modules loaded. It checks the actual UI/header/self identities, parses every container stream, round-trips Definition/Header/Biography/History with SDK typed executors, and reads the portable sheet through the public inspection API. The guarded phase denies file and process access, including late source-file reads.

The final freeze has 28 owned code/test paths. A loaded-source closure contains 3048 repository dependencies and preserves the 20-module shared metadata freeze `ef509d05d4be551a2bb15870d1f1ae6ddf1cb6c9258fcda3eb8e03b2256333b6`. Its immutable private source snapshot independently reproduces the alpha artifact.

Four new designs each run in two isolated SDK processes and one separate independent research process. All seven streams and the entire compressed container agree exactly. All 31 malformed or out-of-profile jobs reject without artifact output. The final 43-process receipt is [SdkBlankDrawingFile01.json](../measurements/2026/SdkBlankDrawingFile01.json).

| Design        | Sheet ratio | Definition bytes | Container SHA-256                                                  |
| ------------- | ----------- | ---------------- | ------------------------------------------------------------------ |
| PortableAlpha | 13:7        | 24055            | `d46ec820a888469e41bc0309c3dd56a83107a1e51f6d9586839a677be2aeaf44` |
| PortableBeta  | 17:11       | 24683            | `61d96e787cb16e74919d61137142df57825bad556f1587c779ac7fca185d0eb2` |
| PortableGamma | 3:19        | 24055            | `d854dca2911793541beff8316510d2095e27dc7b89be08c0cc17382e761eca34` |
| PortableDelta | 23:9        | 25690            | `e1b2c9d1299aea6c6e47a92af0673c7ba8930718e39e22e73cc792645932bd69` |

Beta varies long Unicode/XML text and authoring times. Gamma varies inches, precision and dimension-text linkage. Delta varies sheet text, drafting standard, font, CJK language/save provenance, build code and license-origin category. Each input is authored from the disclosed neutral recipe, without saved native payloads. Earlier development proofs remain private and are not substituted for the final source-bound result.

## Remaining acceptance

This tranche has zero new native measurements and zero held-out reads. Historical research-writer blank/prefix and drawing cohort acceptance remains separate evidence. The public adapter remains read-only. Linked-view assembly of an actual SDK-generated child, broader paper/sheet/content support and any production readiness claim require their own complete construction and native-qualified evidence.

See the [maintained guide](../../../Documentation/Reference/Research/Solidworks/SdkBlankDrawingFile.md) and [change entry](../../../Documentation/Changes/Solidworks/Inspection/Drawings/Portable/SolidworksSdkBlankDrawingFile.md).
