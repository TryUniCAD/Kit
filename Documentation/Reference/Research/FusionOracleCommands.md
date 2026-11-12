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

### Entity properties and session identities

The following query succeeded after a later import of the controlled archive:

```text
PEntity.Properties 203
```

`re/Fusion/LocalOracle/Inspection/Values.json` records parameter properties including `userName`, `expression`, `value`, `unit`, `comment`, `creationIndex`, and inherited `rParent` and `rClientObject` references.
The response identified interface `Ns::Parameters::Parameter` and runtime segment `18`.
The parameter value was `1.9000000000000001`, with expression `19 mm` and user name `betaLength`.

The earlier `segId` value `11` could not be reused: a JSON entity reference containing that stale segment ID failed with `Invalid entity ref`.
Native `JSONGetMembersVisitor::onVisit(Entity)` calls `Segment::sessionWideID` when it writes the response's `segment` property.
These runtime segment identities are not portable identities from the F3D archive.
Resolve them from the current import's `PAsset.EntityIds`, or use the simple entity identifier while the intended asset is active.
Do not carry a numeric `segId` between imports or application sessions.

The later feature capture also rejected the raw JSON reference syntax with current segment IDs.
Consequently, the earlier old-segment failure cannot be attributed solely to stale segment identity.
The successful feature graph export uses positive numeric entity IDs in the active import and explicitly skips named roots.
See `re/Fusion/LocalOracle/Features/GraphCapture.json`: 211, 243, and 243 property records, no numeric-query errors, and 14, 15, and 15 skipped roots.
JSON-reference syntax has not been established as a working command input by these experiments.

`Entity.Dump 203` also succeeded but returned a short inheritance and reference-presence description, not the complete member values.

The `PEntity.Properties` implementation at `0x3430bc` in `NsDataModel10.dylib` also accepts `/limited`, `/skipNulls`, `/followRefs`, `/customOnly`, and `/noCustom`.
`/limited` selects property script identifiers supplied as flags.
`/skipNulls` sets `returnNulls(false)`, and `/followRefs` sets `followStrongRefs(true)`; the latter does not establish that every reference kind is followed.
The simple parameter query is verified; these optional combinations were inspected statically.

### Schema introspection limits

`JSONGetMembersVisitor::onVisit(Member)` at `0x313274` calls the member metatype's `implementJSON` and `includeJSON` hooks before emitting a value.
It can omit a member and uses separate JSON callbacks from the persistence callbacks.
Its keys come from script identifiers, with a uniqueness helper, rather than an exported binary field-order description.
The parameter response is useful semantic evidence, but success does not establish that every persistent member of every class is represented.

`MetaTypes.List` calls `MetaType::toString`, whose recovered format contains the metatype name, version, add-in, base, derived flag, and Neutron flag.
It does not enumerate member intrinsic types.
The schema XML command calls `MemberSet::getMembersInfo`, which emits member count and names.
No richer text-command schema interface was established by the inspected command implementations.
A `MetaTypes.DumpData` string occurs in installed diagnostic text, but that string alone does not establish an available registered command.

Native C++ reflection contains additional schema information:

| Facet                                      | Accessors                                                 |
| ------------------------------------------ | --------------------------------------------------------- |
| Member and scripting identifiers           | `Member::id`, `Member::scriptId`                          |
| Declared C++ type name                     | `Member::debugTypename`                                   |
| In-memory data and implementation offsets  | `Member::offsetToData`, `Member::offsetToImpl`            |
| Metatype and template callbacks            | `Member::meta`, `Member::templatizedFunctions`            |
| Member option bitmask                      | `Member::isSet(EMemberOption)`                            |
| Inheritance and registered member sequence | `MemberSet::base`, `MemberSet::member`, `MemberSet::size` |

In this build, `MemberMetaType::type` reads a category with values `0` intrinsic, `1` collection, `2` pair, `3` value type, `4` strong reference, `5` passive reference, and `6` optional.
The category predicates at `0x18b5d0` through `0x18b630` establish that mapping.
These are native reflection categories, not wire-tag values.
An in-memory offset or C++ type name does not establish serialized field position or byte width.

The vendor schema dumper demonstrates a concrete registry path: `MetaTypeMgr::get`, then `metaTypes(std::vector<MetaType*>&)`, then an RTTI-checked cast from `MetaType` to `EntityMetaType`, followed by `EntityMetaType::memberSet(UINT32_MAX)`.
The final getter returns the existing current member-set pointer; it does not initialize an uninstantiated class.
Null and uninitialized member sets must remain distinguishable from a known empty schema.
The analogous const `ValueMetaType::memberSet` getter also reads an existing set.

The installed owning SDK directories contained no private `MetaType`, `EntityMetaType`, `Member`, or `MemberSet` headers in this investigation.
The symbols use libc++ C++ types, and return-type evidence comes from caller disassembly as well as getter bodies.
`Member::id`, `scriptId`, and `debugTypename` return references to `std::string` objects, not C strings.
The exported `EntityMetaType` RTTI is available, while the examined `MetaType` RTTI symbol is local.
The vendor's cast must not be replaced with an unchecked cast of every registry entry to `EntityMetaType`.
The subsequent research-only [native bridge](../../../re/Fusion/LocalOracle/SchemaBridge.cpp) executes this getter sequence with ABI and runtime identity checks.
Its [evidence record](../../../re/Fusion/LocalOracle/BridgeEvidence.json) separates the documented C++ ABI, installed binary call sites, compile-time layout checks, and runtime guard conditions.
The [first successful capture](../../../re/Fusion/LocalOracle/Reflection/Capture.json) reports return code zero, 1,958 registered types, and zero documents before and after the read-only export.
Of 1,916 unique entity/value member sets, 260 were initialized and exposed 938 fields; uninitialized sets retain null members.
The native bridge reads existing sets only and never invokes schema initializers, segment save/load, or preference mutations.
Its observed success applies to the recorded macOS arm64 build; this is not a public supported Python reflection API.

A generic persistence schema still requires registered definitions, inherited ordering, option meanings, version migrations, custom serializers, and actual load/save callbacks.
The studied classes register their members through `Parameters::Parameter::initializeMemberSet` at `0x16b5d8` and `Parameters::ParameterTable::initializeMemberSet` at `0x170000` in `NsCommonData10.dylib`.
Tracing registrations and template callbacks supplies type evidence beyond property values.
This reference does not expose those C++ methods as an established public Python API.

### Additional unverified diagnostics

The following command names and help were also recovered from the installed binaries but do not have successful capture evidence in this record:

| Command                                   | Intended diagnostic surface                       |
| ----------------------------------------- | ------------------------------------------------- |
| `PEntity.GetEntityInterfaces <EntityRef>` | Direct, base, and supported interfaces            |
| `Document.DumpData [/v /r]`               | Document and asset diagnostics written to the log |

`Document.DumpData` is not a demonstrated export of the whole persisted graph.
Property JSON and XML metadata do not automatically expose custom binary streams or every hidden history state.

The installed `NsMCP10.dylib` also contains `MCP.Server`, `MCP.ServerURL`, `MCP.Port`, and `MCP.EnableTools`.
The observed local server endpoint was not listening, and it was not required for the working bridge.
`MCP.Server /on` writes the application's server-enabled preference; it is not a harmless connectivity query.
No MCP preference change is part of the bootstrap described here.

## Verification boundary

The verified results are the native Python probe, the disposable parameter allocation archives, the active-document schema dump, entity-reference enumeration, one parameter property query, its short entity dump, and the binary segment capture.
The XML segment capture failed in native code; its predicted output structure is static evidence only.
Other commands above are identified from installed code unless separately accompanied by a capture report.
No local automated test suite was executed to produce this reference.
Independent reader/writer output still requires complete semantic comparison and vendor-loadability evidence under the repository's acceptance rules.
