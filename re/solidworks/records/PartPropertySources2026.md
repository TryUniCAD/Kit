# SOLIDWORKS 2026 part property owners

Task B04-SW2026-PARTPROPS, owner `/root`, PR #121.

Two disclosed 2026 SP05.2 designs with different feature graphs and
configuration names were updated through the actual native API. The rectangle
received five summary fields, two document properties and one configuration
property. The circle received three summary fields, three document properties
and two configuration properties. The same name can resolve to an
independent value in each scope. Both designs preserved their full observed
tree and measured solid through save and fresh reopen. Six
distinct native processes passed, including both original controls and
36 numerical comparisons. [Measurement](../measurements/2026/PartPropertySources01.json)

The author invoked `SummaryInfo` through its indexed property dispatch and
used `CustomPropertyManager("")` and the selected configuration manager for
their respective text entries. `Get6` and `GetType2` independently returned
the authored and evaluated string, the text type and the absence of a
property link. The same value, type and scope were observed on fresh reopen.
[SummaryInfo](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.imodeldoc2~summaryinfo.html)
[Add3](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.icustompropertymanager~add3.html)
[2026 property types](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swCustomInfoType_e.html?id=2.10.1.222)

## Wire fields

| Owner | Classification and measured rule |
| --- | --- |
| `docProps/core.xml` | Input text is stored as `dc:title`, `dc:subject`, `dc:creator`, `dc:keywords` and `dc:description`. Native save supplies the last author and modification time as separate fields. The created timestamp remains separate from both. |
| Document and configuration XML root | Constant namespaces distinguish `docProps/custom.xml` and `docProps/Config-0-Properties.xml`. Their section records are outside the default XML namespace. The literal `vt` qualified vocabulary remains bound on both roots. |
| Standard summary section | The document profile includes reserved PID 1 with UTF-8 codepage 65001 and PID 22 false. The configuration summary section has its reserved dictionary entry alone. |
| User section | Reserved PID 1 and the PID-zero dictionary entry occur independently of the authored rows. There is one row per input string, with IDs assigned from 3 in insertion order. A separate native name dictionary orders the measured names lexically and retains the same IDs. |
| Ordinary text row | The `vt:lpstr` child carries the authored input. The observed equation state is false. The compatible text lane stores TypeID 0 and the advanced lane stores TypeID 30. Both report API type 30. |
| Evaluated text | The disclosed document-level lanes carry one `FPVals` entry whose value equals the ordinary literal input. The advanced configuration also carries one value. The compatible configuration saves without `FPVals` and still returns the same resolved text. |
| `Contents/CusProps` | The advanced file contains one keyed container with separate document and configuration property lists. Each text object owns exactly one string element and explicitly holds its name, expression and value. The compatible file contains an empty manager. Both archives round-trip this stream exactly through the research serializer. |

The OLE vocabulary reserves PID 1 for the code page and PID 0 for the
dictionary. PID 22 reports whether hyperlink values changed. The observed
false value is consistent with an ordinary part without hyperlinks.
[CodePage property](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-oleps/b8910736-7f4a-469a-9644-aed68a71d7d1)
[Property identifiers](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-oleps/04727953-c174-4d01-80ae-b38b15d7068a)
[Document summary identifiers](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-oshared/3ef02e83-afef-4b6c-9585-c109edd24e07)

## Native bindings

`sldmfcu.dll` SHA-256
`af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`
exports the core vocabulary at `0x3c78a1c0`, the configuration vocabulary
at `0x3c78a160` and the custom vocabulary at `0x3c78a240`.
The core-save entry at `0x3c8c8f80` initializes the core DOM from its
vocabulary if needed. The property-set writer at `0x3c891920` emits the
section and name dictionary. `GeneratePropertyID` at `0x3c88b3f0` starts
the maximum at 2. The [literal-prefix trace](DrawingPropertyPrefix2026.md)
binds the separate append and namespace behavior. REA observed the original
binary identity in `ev_3fd7a450c618cc5ca54c2f4211b77193d91fe7dc3fc4625c8cd43cfdcadb3f27`.

`sldmodu.dll` SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`
exports the ordinary text-element constructor at `0x4b2feee0`. It installs
the text-element vtable `0x4cdcfb10`, whose slot `+0x28` selects the serializer
at `0x4b2a2560`. The function first invokes the base `su_CObject::Serialize`
import, then checks the archive mode. Both lanes access element `+8`
through the appropriate wide CString store or load bound at
`0x4cd3da28` and `0x4cd3da30`. It consumes one CString and has no
file-version conditional. The complete function `[0x4b2a2560,0x4b2a25ac)`
has SHA-256 `460fef3767dcde87125d80cd3332ef7345ca003c44e20386279a4ea6aad8ce32`.
REA observed the original binary identity in
`ev_dce068421fbd5576d2d720304f0a68a8019d0cd19d551e09922617c41adf388d`.

The [independent source audit](../../tooling/sw2026/serial/AuditPartPropertySources.py)
verifies linked XML and advanced text values against the authored cases. Its
two binary manager streams finish at map counters 23 and 3 from base 1.
Both retain exact bytes with no opaque continuation. The active advanced
container's other controls and policy fields still require independent
classification before fresh advanced graph construction.

The input shapes and native observations were disclosed. The measurement
establishes the text property grammar and source lifecycle. Generated
property edits, alternate value types, advanced graph construction, source
conversion and the held-out writer check remain open.
