# Drawing document-property section construction in SOLIDWORKS 2026

The generated blank reached the native document-properties call and failed to deliver its return stop. Both controls and debugger cleanup passed. Correcting the XML section and name dictionary preserved clean native open and sheet-scale editing, but SaveAs still returned `[false, 1, 0]`. The correction is a source-grounded grammar repair; it is insufficient to repair native saving. [Measured call interval](../measurements/2026/DrawingBlankSavePropertiesEntryNative01.json), [corrected-section native trial](../measurements/2026/DrawingBlankPropertySectionsNative01.json)

## Scope and implementation

The research constructor `builders.PropertySections.text_information_properties` builds ordinary text properties from an ordered mapping. The drawing metadata caller supplies the six existing neutral sheet-index values. It emits one typed property and one dictionary entry per input item. All counts, property IDs, names and values follow from that mapping. The writer reads no native metadata.

The shared call site is `drawing_sheet_indexes` in [DrawingMetadata.py](../../tooling/sw2026/builders/DrawingMetadata.py). The constructor is [PropertySections.py](../../tooling/sw2026/builders/PropertySections.py). This change applies to the research drawing writer. Production writer admission and additional property types remain outside this profile.

## Original implementation evidence

All module addresses below use the original SOLIDWORKS 2026 SP05.2 images.

| Module | SHA-256 |
| --- | --- |
| sldmfcu.dll | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` |
| sldappu.dll | `50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf` |
| slduiu.dll | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` |
| doccplu.dll | `ad0c266a966381defe9a68c11b76dc318acc6a9f6ac428d5aa253049df87ddd8` |

| Rule | Original implementation | Confidence |
| --- | --- | --- |
| Outer `Properties` namespace and `docPropsVTypes` vocabulary | `SldPropertyXMLHelper::getXMLStringForSolidworksInformationProperties` at `sldmfcu!0x3c78a2a0` and its metadata descriptor at `0x3c78a010`. | Confirmed vocabulary in D00 and D01. |
| No-namespace `propertySection`, `fmtid` and `name` | Reader at `0x3c890720` queries `//propertySection`, reads `fmtid` and `name`, and parses the GUID. Store at `0x3c891920` creates the matching node and attributes. | Confirmed source and disclosed records. |
| User-defined section identity | Store compares section GUID with immutable constant `0x3cc6a1b0` and names it `UserDefinedProperties`. Its GUID is `{D5CDD505-2E9C-101B-9397-08002B2CF9AE}`. | Confirmed source and disclosed records. |
| Typed values | Section children named `property` contain `name`, decimal `pid` and a typed child in `http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes`. The type-name map at `0x3c88f6d0` maps variant 30 to `vt:lpstr`. | Confirmed ordinary text framing. |
| Name dictionary | The reader separately visits `propertyNameDictionaryElement` at `0x3c891637`. The store emits these elements at `0x3c89244e/0x3c89254c`, with `name` and matching `pid`. | Confirmed source and disclosed records. |
| Fresh ordinary IDs | `suOlePropertySection::GeneratePropertyID` at `0x3c88b3f0` starts its maximum at 2 and returns one plus the maximum admitted existing ID. Ordinary insertion calls it with EDX zero at `0x3c7cb602`. Fresh neutral entries therefore use 3 onward. | Source proven. The minimal profile opens and edits; save acceptance remains unqualified. |
| Name lookup | `suOlePropertySection::GetID` at `0x3c88b910` uses the section's name dictionary. | Source proven. |
| Optional state attributes | The store emits `status`, `IsEquation` and `TypeID` on their corresponding property states. The ordinary disclosed text entries omit them. | Ordinary absent-state vocabulary confirmed. Other states remain outside the constructor. |

ElementTree emits a prefixed outer namespace and unqualified section, property and dictionary nodes. A serializer that chooses a default outer namespace must explicitly keep those children outside it.

The property-name dictionary is a separate model component. A `name` attribute on a value element alone does not establish its lookup entry. The constructor computes both records from the same neutral item.

## Disclosed control agreement

Only the disclosed D00 and D01 cases contributed to this grammar check. Their source lock is SHA-256 `60dc068659185e981419d7a09006dd8358fb46896150fad8dcc8cb8414d4f1a7`.

| Case | Native file SHA-256 | Property XML SHA-256 |
| --- | --- | --- |
| D00EmptySheet | `227f12b5834f73e31d1cb64db9e615418852bfba6c30d6c2700be6e26cc4932b` | `3aa23a5fee27d5cbfa55e201c514be9fad8fcd9914e7b7b38399611d74e0f7e3` |
| D01FrontView | `2fd1d31f7f957def7fd2c73b3b88295aecb56c41d29dc208445b711c3d50c525` | `090e5e039c675d832740320363737fc16c0e8f76c9e7e43b008e64f591c89d9e` |

Both documents use the same section name, GUID, namespaces and dictionary framing. Each has 60 typed value records and 83 name-dictionary records. The value kinds include i2, i4, r8 and lpstr. Those counts and rows are discovery evidence. The constructor uses the input mapping's length and insertion order.

## Load and save owner

`uiBaseDoc_c` allocates a fresh 0x218-byte `suDocumentProperties` at `sldappu!0x458e451b` and stores it at document `+0x448` at `0x458e4526`. The property constructor creates its general and SOLIDWORKS property bags and starts summary owner `+0x1d8` and XML caches `+0x1f8..+0x210` null.

`LoadDocumentProperties` calls that owner's `LoadFromStorage` at `sldappu!0x458e6340`. The implementation at `sldmfcu!0x3c7c9d40` loads XML and populates the summary owner from storage slot `+0x230` at `0x3c7ca40e/0x3c7ca414`. The ordinary ZIP summary factory at `0x3c8b7590` constructs `CZipStorageSummInfo` as needed.

The measured save call at `doccplu+0x1df56` resolves to `sldappu!uiBaseDoc_c::SaveDocumentProperties` at `0x458e7590`. It passes the owner at `+0x448` to `suDocumentProperties::SaveToStorage` at `0x458e76af`, resolving to `sldmfcu!0x3c7ca630`. A negative fallback `StgOpenStorage` HRESULT at `0x458e769b` reaches the throw helper at `0x458e7704`. Ordinary scalar-zero returns are discarded by the outer caller. The exact runtime failing instruction remains unmeasured.

## Verification and native result

The exact original neutral request has SHA-256 `fb9e098382aa68bc8232bc7adebb3a02183fd9244de082086d1b5dd143e94362`. Two separate guarded generator processes produced identical corrected files with SHA-256 `7400cf1fa4a71994807ce8e49283e2721e09a5ceaf723e36f6ae807906c94a26`. Both recorded zero runtime input-file access attempts.

The seven stream roles match the earlier failing candidate. Only `docProps/ISolidWorksInformation.xml` changed. The Definition, Header2, model stamps, history, biography and keywords remain byte-identical. Structural readback found six typed text records, six matching dictionary entries and IDs 3 through 8. The existing public drawing reader retained the intended sheet, dimensions and scale.

The native packet uses the existing committed `PrepareBlankDrawing.py` and `InspectBlankDrawing.py` tools. Its trial SHA-256 is `e0aab1bbdac876403626aa2a35fb41c1569fab326e63f051c00474263ac09301`. It retains pristine, repacked and reduced-native controls, the exact encoded generated path, sheet-scale editing, actual SaveAs and fresh reopen.

The completed trial used nine distinct native processes. Both pristine brackets and the repacked and reduced-native controls saved and reopened with zero errors and warnings. The corrected generated file opened with zero errors and warnings and accepted the sheet-scale edit, then returned SaveAs `[false, 1, 0]`; no fresh reopen followed that failed save. The trial was interpretable and exited 3. The private result SHA-256 is `3e812322931dbaf696dfb56fc25ca23d22be3e75290bb4b2f30223159b96e784`; the host transport SHA-256 is `d37226b31d7b976bc04117886fe566f16bb6a9634fc1f02c1c869bb97eea96df`. [Sanitized native receipt](../measurements/2026/DrawingBlankPropertySectionsNative01.json)

This refutes the hypothesis that correcting section framing, fresh IDs and name dictionaries alone repairs the blank drawing's save failure. It does not refute the independently traced grammar. The exact failing instruction inside the document-properties call, including summary-storage initialization and fallback-storage hypotheses, remains unmeasured.

[InspectBlankDrawingPropertySections.py](../../tooling/sw2026/InspectBlankDrawingPropertySections.py) adds verification of the frozen request, construction and comparison receipts before native startup. It requires both packet and runner hashes. Its successful exit requires the generated case and controls to pass. The base observer's interpretable status remains a separate field.

REA evidence IDs include `ev_33a400649bb6d7b2ddc0a63ef9d835faa10eda89ce02ccec614fb38ec4063cb0`, `ev_43051a5930aa820c8fb6282ef333dd06de42ee3b651ecb6d9a35c96aebd0fb1b`, `ev_7321c68bb617805fc7759a4eaa7d0a6412770de1df4fb7e887c238d754f71566`, `ev_60dacbe63f3269bf0ac939fd470582937adb3d74b654c590c865705a7eb869f3`, `ev_22e8deb47c5260aabeaf2ccbc81caf671d3632b9ad195fbe6ee477266cc3110e` and `ev_f9b569d4fc72f9a950abb02eadb5ab76c7814899b25f02c6274f1db85dd70202`. The bounded task-owned target was closed after these queries.
