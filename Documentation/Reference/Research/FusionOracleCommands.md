# Fusion local oracle commands

## Scope and evidence

An installed Fusion process can execute an isolated Python capture script through its existing frontend command bridge.
This research used Fusion `2706.1.17` on macOS arm64 after explicit authorization for controlled local oracle captures.
It did not require a GUI driver, a registered add-in, or enabling the Fusion MCP server.

The bridge is an internal interface shipped with Fusion, reached through a local Chromium debugging transport.
It is not established here as a supported public external automation API, a headless mode, or a stable interface across releases.
Kit's production reader and writer must remain independent of the Fusion runtime.
Successful oracle execution is evidence about the vendor's data model; it does not establish independent generation, complete decoding, or target-application acceptance.
See the [persistence data model](FusionDataModel.md) and [oracle requirements](Oracles.md).

The inspected installation was under:

```text
~/Library/Application Support/Autodesk/webdeploy/production/b43a07003c01dd54425db484d23b1c5e6248a21d/Autodesk Fusion.app/Contents
```

Paths below are relative to that `Contents` directory.
Native addresses identify symbols in the arm64 Mach-O slice before runtime relocation; they are not process addresses or universal-binary file offsets.
They are evidence anchors for this build, not addresses that automation should call.

## Dispatching a capture script

The running process exposed a Chromium target list at `http://127.0.0.1:9766/json/list`.
The Fusion home target had a URL under `https://ui-dls360.autodesk.com/fcdr/fusion-home-tab/`.
Its target identifier and WebSocket URL are session-specific and must be discovered rather than copied from a previous capture.
The existence of this listener in the studied session does not establish that every installation enables it.

The installed home frontend contains the native bridge wrapper in:

```text
Resources/FusionCDEHostApps/fusion-home-tab/bundle.aae5d9dd82739a0c3062.js
```

The frontend waits for `window.neutronJavaScriptObject` and serializes command arguments as JSON.
The following expression, dispatched in that target through its local debugging transport, successfully reached Fusion's Python runtime:

```javascript
window.neutronJavaScriptObject.executeCommand(
  "RunScriptCommand",
  JSON.stringify({ Path: "/absolute/path/to/Capture.py" }),
);
```

`Path` is case-sensitive in the recovered argument contract.
It is a root JSON property containing a string, not a nested argument object or a command-line suffix.
Supplying a nonempty path avoids the command's file dialog.
The command is registered in `Libraries/Neutron/Neutron/UI/Commands/Resources/CommandDefinitions/CommandDefinitions.xml` with identifier `RunScriptCommand` and the description “Run a python script”.

The native execution chain is:

| Library                | Symbol                                  | Address    | Observed responsibility                                       |
| ---------------------- | --------------------------------------- | ---------- | ------------------------------------------------------------- |
| `NuBase10.dylib`       | `Nu::JavaScriptObject::_executeCommand` | `0x79da5c` | Builds a command context from JSON and posts a command event  |
| `NuClientBase10.dylib` | `Nu::CommandContext::pathArgumentName`  | `0x96028`  | Returns the exact argument name `Path`                        |
| `NuClientBase10.dylib` | `Nu::CommandContext::argumentsFromJSON` | `0x96a7c`  | Converts root JSON properties into command arguments          |
| `NuBase10.dylib`       | `QTJavaScriptCommandHandler::event`     | `0x79f42c` | Dispatches the command through `CommandMgr`                   |
| `NuCommands10.dylib`   | `RunScriptCmd::onExecute`               | `0x30bc28` | Reads the path and creates a Python task                      |
| `NuCommands10.dylib`   | `RunPythonTask::make`                   | `0x30be98` | Adds the task to the application task queue                   |
| `NuCommands10.dylib`   | `RunPythonTask::onExecute`              | `0x30bf0c` | Calls `PythonManager::runScriptFile`                          |
| `NsBase10.dylib`       | `PythonManager::runScriptFile`          | `0x1ad708` | Reads the file and submits its source for execution           |
| `NsBase10.dylib`       | `PythonManager::runScript`              | `0x1abf98` | Selects the shared `__main__` module                          |
| `NsBase10.dylib`       | `PythonManager::runScriptEx`            | `0x1ac7a0` | Uses the module dictionary to compile and evaluate the source |

These libraries reside in `Libraries/Neutron/`.
Static inspection used exported symbols and disassembly without modifying the installed application.

### Completion and Python context

The JavaScript call dispatches asynchronously.
Its return value is not a completion result, and a successful transport response does not prove that the script ran successfully.
The queued task executes the Python source after the dispatch returns.
An unhandled Python failure can be surfaced through a native message box rather than the WebSocket result.

The source runs at top level in a shared `__main__` dictionary.
The loader does not import the script as a module and does not automatically invoke a function named `run(context)`.
Top-level names can remain between invocations.
Use explicitly invoked capture functions with local variables and unique output paths.

`__file__` was absent in the first probe.
That probe produced no completion file until its output path was made absolute.
Use absolute input and output paths rather than deriving paths from `__file__` or assuming the process working directory.
Capture exceptions into an explicit report and require that report before interpreting a dispatch as complete.

The successful probe recorded:

```json
{
  "fusion_version": "2706.1.17",
  "documents": 0,
  "active_document": false,
  "status": "application_api_reached"
}
```

The local evidence is `re/Fusion/LocalOracle/ProbeResult.json`.
The following allocation capture created a disposable parametric design, exported four states, and closed that design without saving it to the user's documents.
Its `finally` path restores the original document if one existed and remained valid.
The initial session had no open documents.

## Metadata schema commands

Use the ordinary in-process API `adsk.core.Application.get().executeTextCommand(...)` after the script has reached Fusion.
The following exact command spelling succeeded:

```text
Document.DumpAcitveDocSchema "/absolute/path/to/ParameterSchema.xml"
```

The transposed letters in `Acitve` are part of the registered name.
Correcting the spelling to `Active` changes the command.
`TextCmdDocumentDumpAcitveDocSchema::execute` is at `0x27fc64` in `NuCommands10.dylib`.

The capture returned a success message identifying the requested path and produced a 103,248-byte UTF-16 XML document.
Its root was `MetaTypes`, with 155 immediate metatype records.
Each record carried attributes including `Name`, `_ID`, `_Version`, `_BaseID`, `_AddInMod`, `_Derived`, `_InternalType`, and `_Valid`.
Member-set information was text within the record, not a complete machine-readable wire layout.

For example, `ParameterTableMetaType` had identifier `B0556F58-EE09-46A7-B18F-E296F48E5B13`, version `4`, add-in `CommonData`, and these five registered members:

```text
bIsStateChangedByUser expandedNodeSet groupOrder highWaterMark rParameterSearchByNameHelper
```

This confirms native names and inheritance metadata for types encountered by this document.
It does not by itself determine field widths, wire offsets, custom serializers, uninstantiated feature classes, or ASM body encoding.

The local evidence is under `re/Fusion/LocalOracle/Allocation/`: `Capture.json`, `ParameterSchema.xml`, `empty.f3d`, `two_parameters.f3d`, `deleted_first.f3d`, and `added_third.f3d`.
The report records archive digests, parameter names, expressions, values, units, and timeline counts.
Those archives are vendor-authored controls, not independently generated acceptance candidates.

Two related command names were recovered statically but were not validated by that capture:

| Command                                                                                  | Scope and limitation                                                                              |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `Document.DumpOpenedDocsSchema <xmlFileName>`                                            | Collects schemas from open documents; may include unrelated user documents                        |
| `Document.DumpDocSchemaByFile <File> <xmlFileName> [/F] [/D] [/f3d] [/sim360] [/cam360]` | Opens files while collecting schemas; `/F` selects a file and the default is directory processing |

These are not interchangeable with a full entity-graph export.

## Segment stream export

`Segment.Save "/absolute/path/to/Design.xml"` writes to the exact supplied filename.
The filename extension does not choose the format.
An observed invocation returned `Ok` but wrote a ZIP archive containing `BulkStream.dat` and `MetaStream.dat`, despite the `.xml` suffix.

`TextCmdSegmentSave::execute` at `0x27b754` in `NsDataModel10.dylib` constructs a `SegmentFinder`, attaches a `SegmentTestor`, and calls `Segment::save`.
The `SegmentTestor` constructor's final Boolean means loading versus saving; it is not a binary-format selector.
The command's help mentions `/Binary`, but the inspected implementation does not consult that flag.

### XML option and failed capture

The exact option command is:

```text
Options.BinaryPersistence
Options.BinaryPersistence /off
Options.BinaryPersistence /on
```

With no flags it reads the setting and returns `Binary Persistence is on` or `Binary Persistence is off`.
`/off` selects XML persistence; `/on` selects binary persistence.
The command implementation is `TextCmdOptionsBinaryPersistence::execute` at `0x17e538` in `NsBase10.dylib`.
`SegmentImpl::isBinary` at `0x269174` consults this option while a `SegmentTestor` is attached.

The attempted XML capture switched this setting off and called `Segment.Save`, with restoration planned in `finally`.
The native call crashed before producing the requested XML or the completion report.
Python's `finally` did not establish restoration after this native failure.
After process recovery, [Restore.json](../../../re/Fusion/LocalOracle/Restore.json) confirmed binary persistence was on and zero documents were open.
This sequence is therefore a failed research experiment, not a validated XML export recipe.
Any subsequent controlled attempt must account for process failure and verify the prior option state after recovery; `try/finally` alone is insufficient.
Do not assume the initial state is on or pass both flags.

The underlying setter, `PersistenceOptionGroup::binaryPersistence(bool)` at `0x108218` in `NsBaseCore10.dylib`, updates a Boolean and invokes change observers.
The text command does not directly call an options-save operation, but those observers were not fully traced.
The change must therefore not be described as guaranteed memory-only or incapable of persistence.

Static inspection identifies two output branches; only the binary branch succeeded in the recorded capture:

| Format | Destination and structure                                                                                                                                                |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Binary | A ZIP package at the exact requested path; the observed capture contained the binary bulk and metadata streams                                                           |
| XML    | The code constructs one XML document at the exact requested path, with a `Segment` root containing imported bulk and metadata stream roots; the attempted capture failed |

`SegmentTestor::xmlDocument` at `0x25de18` creates the `Segment` root.
`XmlBulkStream::terminate` at `0x29f4f8` and `XmlMetaStream::terminate` at `0x2a364c` append their stream roots to it.
`SegmentTestor::save` at `0x25dccc` passes the stored path directly to `XMLDocument::save`.
This does not create separate `BulkStream.xml` and `MetaStream.xml` files beside the requested output.

### Selecting the segment

The command does not explicitly request the active UI design.
`SegmentFinder::SegmentFinder` at `0x27356c` follows this order when asked to use an existing segment:

1. Reuse its cached segment pointer if present.
2. Otherwise, use its explicitly selected asset if present.
3. Otherwise, take the last document in `DocumentMgr`.
4. Take that document's active asset, or its last asset if no asset is active.
5. Request segment type `1`, identified as `Design` in the inspected build.

The cache and selected asset are native process state, exposed as `SegmentFinder::c_pLastPrimarySegment` and `SegmentFinder::c_pExistingAsset` in the inspected symbols.
An invocation can therefore target something different from the visible document.
Keep the oracle's disposable document ownership explicit and inspect exported entity content before attributing a capture to it.
Creating a new document is insufficient evidence if the finder already has a cached segment.

`Segment.SetCurrent`, `Segment.GetCurrent`, and `Segment.ClearCurrent` were also recovered, but they operate on `TextCommandsContext` objects identified by session-wide IDs.
The inspected `SegmentFinder` uses separate storage.
No connection between those two stores was established, so these commands are not a verified way to select the target of `Segment.Save`.
Do not clear or replace a user's native selection based only on the similar command names.

`Segment.Save` calls native persistence routines and updates persistence state; treat it as a capture operation on disposable documents, not as a guaranteed read-only inspection command.
`Segment.Load` mutates the selected segment and was not needed for these captures.

The failed XML attempt's sampled stack placed the fault context at `SegmentTestor::SegmentTestor + 104`, called by `TextCmdSegmentSave::execute`.
It also showed the capture's `RunPythonTask` nested inside an earlier `RunPythonTask` message-box event loop.
The earlier failed probe had left a native error dialog pending.
A previously saved segment's disposable document had also been closed before the XML attempt.
Reentrant task execution and cached segment lifetime are investigative leads, not established crash causes.
The local stack evidence was recorded at `/tmp/kit-fusion-native-analysis/FusionSample.txt`; it is session evidence rather than a portable fixture.

## Other recovered diagnostics

`PAsset.EntityIds` was subsequently captured in `re/Fusion/LocalOracle/Inspection/Inspection.json`.
It returned 203 entity references in segment `11`, including 13 named roots, from the disposable two-parameter design.
Each JSON reference had `segId`, `entityId`, and `rootId` fields.
The same report recorded successful `computeAll()` and the binary `Segment.Save` result.

The following command names and help were also recovered from the installed binaries but do not have successful capture evidence in this record:

| Command                                                    | Intended diagnostic surface                                               |
| ---------------------------------------------------------- | ------------------------------------------------------------------------- |
| `PEntity.Properties <EntityRef>`                           | Entity properties, with optional reference-following and property filters |
| `PEntity.GetEntityInterfaces <EntityRef>`                  | Direct, base, and supported interfaces                                    |
| `Entity.Dump <EntityId> <AssetName> <DocumentDisplayName>` | An entity dump with optional asset and document qualification             |
| `Document.DumpData [/v /r]`                                | Document and asset diagnostics written to the log                         |

`Document.DumpData` is not a demonstrated export of the whole persisted graph.
Property JSON and XML metadata do not automatically expose custom binary streams or every hidden history state.

The installed `NsMCP10.dylib` also contains `MCP.Server`, `MCP.ServerURL`, `MCP.Port`, and `MCP.EnableTools`.
The observed local server endpoint was not listening, and it was not required for the working bridge.
`MCP.Server /on` writes the application's server-enabled preference; it is not a harmless connectivity query.
No MCP preference change is part of the bootstrap described here.

## Verification boundary

The verified results are the native Python probe, the disposable parameter allocation archives, the active-document schema dump, entity-reference enumeration, and the binary segment capture.
The XML segment capture failed in native code; its predicted output structure is static evidence only.
Other commands above are identified from installed code unless separately accompanied by a capture report.
No production Kit code or local test suite was executed to produce this reference.
Independent reader/writer output still requires complete semantic comparison and vendor-loadability evidence under the repository's acceptance rules.
