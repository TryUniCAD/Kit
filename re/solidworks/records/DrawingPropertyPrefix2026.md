# SOLIDWORKS 2026 property-value prefix construction

The generated blank's save failure is isolated to the SolidWorks property-bag call. General custom properties and summary properties returned one on both native and generated inputs. The retained SolidWorks bag was nonnull, used XML mode one and held a nonnull DOM on both. The native call returned one; the generated return stop was armed but not delivered before actual SaveAs returned `[false, 1, 0]`. All seven processes, controls and debugger cleanup passed. This establishes the call interval, not a specific exception. [Native bracket receipt](../measurements/2026/DrawingBlankPropertySaveBracketsNative01.json)

## Source-derived prefix rule

All following addresses refer to `sldmfcu.dll` SHA-256 `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`, SOLIDWORKS 2026 SP05.2.

| Rule | Source authority |
| --- | --- |
| The constructor's SolidWorks-information XML vocabulary explicitly binds `vt` to `http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes`. | `SldPropertyXMLHelper::getXMLStringForSolidworksInformationProperties`, `0x3c78a2a0`. |
| Property-set `+0xa0` is the retained XML DOM. The stream loader writes the supplied document to that owner. | XML branch of `0x3c8901b0`, `loadXMLFromStream` calls with the address of `this+0xa0`. |
| Saving initializes a DOM from the constructor vocabulary only when the existing DOM is null. | `0x3c891a28..0x3c891a40` and initializer `0x3c88b310`. |
| The type-name map emits literal qualified names such as `vt:lpstr`. | `0x3c88f6d0`, used by property-store helper `0x3c891920`. |
| The ordinary element-appending overload selects the `createElement` route rather than the namespace-aware `createNode` route. | `0x3c92b4a0` supplies a zero selector to `0x3c92b760`; the latter uses DOM virtual slot `+0x178` with the tag name and element output. |
| The rebuilt XML is reparsed before saving. A negative load HRESULT or parse-error output flag reaches a `CFileException` throw block. | `0x3c892689..0x3c89269a`, throw block `0x3c892755`, call `0x3c892790`, MSVC throw metadata `0x3cd40838`. This branch has not been measured in the failing process. |

Microsoft's MSXML contract independently states that `createElement` does not assign a namespace URI, including when the supplied name contains a prefix. The namespace-aware operation is `createNode`. A retained document that binds only another prefix does not supply the serializer's literal `vt` declaration. [MSXML createElement](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms757047(v=vs.85))

The previous generated XML was namespace-correct for reading: ElementTree emitted `ns1:lpstr` with the proper URI. It did not declare `vt`. The current constructor supplies an explicit `xmlns:vt` attribute on this document's root and creates literal `vt:lpstr` children. Section, value, dictionary, names, IDs and text come from the same neutral mapping. The change calls no global namespace registration and copies no saved rows, defaults, native IDs or XML template.

## Property owners and initialization

For a `suDocumentProperties` owner `P`, general custom properties are embedded at `P+0x8`; the SolidWorks custom-properties wrapper is the pointer at `P+0x1e0`. Each wrapper's property set starts at wrapper `+0x10`. Its XML mode is the four-byte member at set `+0xb8`; its DOM is the pointer at set `+0xa0`. The summary owner is the separate pointer at `P+0x1d8` and has its own core-property DOM at summary `+0x60`.

The document-properties constructor configures the general bag with custom-property XML vocabulary and the SolidWorks bag with SolidWorks-information XML vocabulary, then sets both property-set modes to one at `0x3c7c929a` and `0x3c7c934b`. `SetPropsXMLData` at `0x3c88e330` retains the XML construction text at property-set `+0xb0` and its descriptor at `+0xa8`; it does not replace an already loaded DOM. A missing stream can therefore use lazy initialization while a present stream remains the edit/save DOM.

The ordinary outer arguments are custom-data zero and option zero. Option zero includes XML-cache setup and both bags. Custom-data zero skips `moXmlDataExtracter`. App, relationships, content types and open-time DOM caches are separate members at `P+0x1f8`, `P+0x200`, `P+0x208` and `P+0x210`. They are not substitutes for the SolidWorks bag's DOM.

The measured bracket result agrees with those independent lifecycles: both general-property DOMs were null before their save, while both SolidWorks-property DOMs were nonnull. The ZIP summary getter creates its summary owner as needed without requiring an existing core-XML stream. Missing XML alone is not evidence of a null summary owner. [Earlier storage-mode receipt](../measurements/2026/DrawingBlankPropertyStorageModeNative01.json)

## Exact failed baseline and prefix-only candidate

The prior section/dictionary correction produced generated file SHA-256 `7400cf1fa4a71994807ce8e49283e2721e09a5ceaf723e36f6ae807906c94a26`. Its nine-process native trial had healthy pristine, repacked and reduced-native controls. It opened and accepted a scale edit but SaveAs returned `[false, 1, 0]`. That result refuted section framing as a sufficient save repair. [Section-correction receipt](../measurements/2026/DrawingBlankPropertySectionsNative01.json), [section field rules](DrawingPropertySections2026.md)

The unchanged neutral request SHA-256 is `fb9e098382aa68bc8232bc7adebb3a02183fd9244de082086d1b5dd143e94362`. Two guarded generator subprocesses emitted identical 6,046-byte prefix-corrected files, SHA-256 `2ac13e616a8853add228bd11e21c400cb461b535bb9fc19252bb848bb410d1b4`, with zero runtime input-file access attempts. Only `docProps/ISolidWorksInformation.xml` changed among seven logical streams. Its parsed expanded XML tree is identical to the failed baseline: the six values, six name-dictionary entries and IDs 3 through 8 are unchanged. This is a lexical prefix declaration change from a source rule, not fitted property values.

A host generic-DOM replay loaded each generated property document, created a literal `vt:lpstr` element with the standard DOM `createElement` operation and reparsed its serialized result. The previous prefix binding produced an unbound-prefix parse error; the per-tree `vt` binding parsed successfully. A separate constructor/serializer/parser pass preserved independently supplied quoted names, ampersands and markup text. This replay tests the XML namespace mechanism independently of the native oracle. Its private receipt SHA-256 is `cb533ef4cdacb09084f187dbfea5f335797297429f76c06b421ab77d32876a59`.

## Controlled native save and reopen

The [property-prefix observer](../../tooling/sw2026/InspectBlankDrawingPropertyPrefix.py) checked the exact request, guarded construction, source snapshot, semantic comparison, candidate, control and observer digests. The corrected drawing passed all ten phases on SOLIDWORKS 2026 SP05.2 (34.5.2.0604). The generated sheet rebuilt at its original scale of 2:3 and accepted an edit to 3:2. Native SaveAs returned `[true, 0, 0]` and wrote a 16,178-byte derivative. A separate process reopened that derivative at 3:2 and reproduced all ten feature rows. Both generated phases reported zero open errors, open warnings and rebuild diagnostics.

The pristine controls before and after the trial, repacked control and same-role reduced native drawing passed all eight corresponding phases. All ten process identities and raw hashes match the host supervisor. The SDK's partial layout reader independently recovered the edited sheet dimensions and scale from the native derivative. [Native receipt](../measurements/2026/DrawingBlankPropertyPrefixNative01.json)

This comparison establishes the prefix rule for a disclosed single unformatted empty sheet. A separate [linked part-view trial](DrawingFrontPropertyPrefix2026.md) passes native position edit, save and fresh reopen with its generated child. The two sealed drawing cases remain untouched and production writer qualification remains open.

REA evidence includes `ev_60dacbe63f3269bf0ac939fd470582937adb3d74b654c590c865705a7eb869f3`, `ev_8b08b791a84504e2f05c7d51fe6b237171f7782b21966950f1c75018cc6f93cd`, `ev_481b9810e5c502f4e60bfafa0020114599b3ce74ecabf36055d318119806f62a`, `ev_763934d257d478c82a3b65cf958eae66489d1af703664badb659d12d09051d6b`, `ev_fbb0ac6c33130a3d4b4ae8c43b0d0e17f39da5bbd2e31887d31d22f97d2224ff` and `ev_c84b5a1a796c1fee064c204a8479ee489d389f0181d85f37326420830b9539bc`. The bounded task-owned Hopper target was closed.
