# Disclosed drawing-edge COM lifecycle

This packet is ready for the root-owned vendor oracle. It has not run SOLIDWORKS and does not qualify a downstream cache or a public drawing writer.

## Frozen inputs and scope

`NativePacket03/Trial.json` is SHA-256 `36143744fc79f19fb60434d24884288f72733e764ed9fd8a8138aff4233d0872`. `NativePacket03/Files.json` is SHA-256 `c7b49f275a7cf4b843ef1522b4b759fa4fbd5342acc3055fd47b543f28da5cf2`.

The native control is the disclosed original D01 Front drawing and its original 20 × 10 × 7 mm child. The generated pair is the already qualified SDK LinkedFrontAlpha drawing and centered 37.9 × 22.7 × 14.3 mm child. All four input files are hash-verified copies of the prior packet. No writer or neutral conversion executes in this trial. Their previous acceptance does not transfer to edge annotations or to a generated downstream cache.

The candidate requests the unique actual visible analytic line joining `(-18.95,-11.35,0)` to `(-18.95,11.35,0)` mm. The native control requests `(0,0,0)` to `(0,10,0)` mm. Endpoints are unordered; the exact 2026 API documents that an edge has no intrinsic start/end direction. Enumeration ordinals never select an edge.

The native view must resolve exactly the approved physical child bytes and configuration, with one visible component and one solid. The selected edge's actual component must match that view component. The existing drawing snapshot compares complete sheet/view state, canonical Front transform, scale, analytic volume, area, centre of mass, and the complete drawing tree. The candidate child tree and depth are derived from the existing neutral request and established COM presentation rule. The control tree is retained in full, checked across rebuild and fresh reopen, and used unchanged by the trailing control.

## Lifecycle

1. Fresh pristine native control: open/rebuild cleanly; read document preference 779/option0; set true and read true; select the real edge by endpoints; insert a note, attach it to that edge, and move/edit it from `edge a` to `edge b` at explicit sheet coordinates; require one non-null edge attachment, correct actual identity, and `IsDangling=False`; rebuild; obtain and resolve the edge's persistent reference; save a nonempty derivative with `(True,0,0)`.
2. Fresh process: reopen that derivative, require preference true, find the exact saved note on the actual view by its native annotation name, repeat text/position/non-dangling/attachment/geometry/tree checks, and resolve the original persistent edge reference.
3. Run those same two phases for the exact generated pair only after both native control phases pass.
4. Run the same two pristine native control phases afterward regardless of the candidate verdict.

The batch passes only with six distinct process-creation identities, all six phases successful, both healthy controls, exact input custody, and unchanged encoded candidate slots. Any missing API behavior, nonunique edge, unsupported attachment, persistence error, warning, tree difference, modal, or cleanup diagnostic remains a failure. It is never converted into a guessed attachment or an ordinal fallback. The trial's `native_acceptance` remains false and `cache_consumer_measured` remains false even if its COM lifecycle passes.

## Exact API binding

The original no-CAD query is SHA-256 `92235db40b63b95246f2479a9166ecaa12c242d3f96d149e13827d1e92b756f5` with Windows line endings. The [LF-normalized receipt](../measurements/2026/DrawingEdgeApiMetadata01.json) is SHA-256 `4ec29582a96d7e6d76464814d46e817ccb55bbf870be4e39dd21be05e3cee0af`. It inspected the registered `{83A33D31-27C5-11CE-BFD4-00400513BB57}` 34.0 wrapper SHA-256 `d8982a8caef31e4c62ed49b70d3747f701fee0622bbaec7a550d6e874327e959`, with zero CAD objects, processes, or documents. It proves the exact method/property forms used by the new observer, including:

- `IView.GetVisibleComponents()`, `GetVisibleEntities2(component, swViewEntityType_Edge=1)` and `SelectEntity(entity, AppendFlag)`
- `IModelDoc2.InsertNote(text)` and `IAnnotation.SetAttachedEntities(variant array)`
- `INote.SetText(text)`, `IAnnotation.SetPosition2(x,y,z)`, `GetPosition()`, `GetAttachedEntities3()`, `GetAttachedEntityTypes()`, `IsDangling()`
- `IAnnotation.GetSpecificAnnotation()` is used before the `INote` cast; an annotation is not cast directly to its lower-level specific object
- `IModelDocExtension.GetPersistReference3(object)` and `GetObjectByPersistReference3(variant byte array, out error)`
- `IModelDocExtension.GetUserPreferenceToggle(UserPref,UserPrefOption)` and `SetUserPreferenceToggle(UserPref,UserPrefOption,Value)`
- `ISldWorks.IsSame(object1,object2)` must return `swObjectSame=1`; unsupported equality is not accepted as true

The visible-entity enum and annotation-attachment enum are different domains even though both ordinary edge members happen to equal 1. The attachment comparison uses `swSelectType_e.swSelEDGES=1`.

SOLIDWORKS' official [persistent-reference guide](https://help.solidworks.com/2026/english/api/sldworksapiprogguide/Overview/Persistent_Reference_IDs.htm?id=1.4.45) documents session persistence for selectable objects. Its [2026 resolver](https://help.solidworks.com/2026/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IModelDocExtension~GetObjectByPersistReference3.html) identifies the model-owned byte array and separate error result. The [2026 endpoint documentation](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IEdge~GetEndVertex.html) requires direction-independent endpoint matching. The official [note example](https://help.solidworks.com/2020/english/api/sldworksapi/Insert_a_Note_Example_VB.htm) demonstrates an edge-attached note and position edit; exact 2026 shapes come from the pinned local query, not that historical example. [SetAttachedEntities](https://help.solidworks.com/2019/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.iannotation~setattachedentities.html) explicitly requires checking whether the chosen annotation/entity pairing is supported, which is why the native control runs first.

## Document option producer

The numeric source record `DrawingEdgePreferenceProducer2026.json` binds the full original `sldappu.dll` and `slduiu.dll`, four complete native owner functions, eight selected windows, and four exact selector/table cells. Getter preference779 reaches `moModel.getDetailDefs`, then reads its i32+0x220 at `0x49296455`. Setter preference779 selects `0x492a914d`, writes the new supplied value at `0x492a9181`, and passes old/new f220 plus the independently retained f224 into the UI callback. Preference780 selects and owns f224 separately. No universal default or optional callback effect is inferred. The intermediate concrete extension-wrapper virtual owner remains a separately stated static boundary; the harness also requires the real public setter's success and public readback.

Existing `DownstreamLinkedDrawingSave2026` proves that nonzero f220 permits storing actual drawing edge-map count f1570/n1578; zero emits a zero count. Setting f220 does not prove that a useful map was populated or that the intended child f380 was consumed.

## Run commands

The root stages this packet without changing its bytes and commits the independently authored oracle scripts before running the native trial.

Host-only preparation used `/opt/homebrew/bin/python3` (3.14), not `/usr/bin/python3` (3.9). The first unused staging directories `NativePacket01` and `NativePacket02` contain partial host preparations only and must not run. `NativePacket03` is the first fully prepared and verified packet.

```sh
prlctl exec --current-user "Windows 11" python -B "\\Mac\Home\Documents\UniCAD\Oracle121Takeover\DrawingEdgeQualification01\NativePacket03\Tools\InspectDrawingEdgeQualification01.py" verify "\\Mac\Home\Documents\UniCAD\Oracle121Takeover\DrawingEdgeQualification01\NativePacket03\Trial.json" --sha256 36143744fc79f19fb60434d24884288f72733e764ed9fd8a8138aff4233d0872
prlctl exec --current-user "Windows 11" python -B "\\Mac\Home\Documents\UniCAD\Oracle121Takeover\DrawingEdgeQualification01\NativePacket03\Tools\InspectDrawingEdgeQualification01.py" run "\\Mac\Home\Documents\UniCAD\Oracle121Takeover\DrawingEdgeQualification01\NativePacket03\Trial.json" --sha256 36143744fc79f19fb60434d24884288f72733e764ed9fd8a8138aff4233d0872
```

Terminal/progress: `NativePacket03/Inspection/Result.json`. Per-phase `Record.json`, `Result.json`, transport records, saved derivatives, and private persistent-reference state are retained under that new directory. No sink mutates files. No global setting, license process, or other session is changed. `Swapp` rejects an occupied oracle and closes only the fresh COM-owned session gracefully. Each worker is bounded at 240 seconds. A timeout or uncertain exit remains failed/uninterpretable; this harness does not kill the vendor app or license services.

The generated drawing references these exact existing guest slots:

- `C:\Users\Public\Documents\KitOracle\SdkLinkedDrawing01\Inputs\LinkedFrontAlpha\LinkedFrontAlpha.SLDDRW`, SHA-256 `306c6a7aaced9957780bda65a5dc87a47f3de4f50d0fe008d8461dd53c6b4dee`
- `C:\Users\Public\Documents\KitOracle\SdkLinkedDrawing01\Inputs\LinkedFrontAlpha\LinkedFrontAlphaChild.SLDPRT`, SHA-256 `251e91656acb06a2ed17f50b9e45676b455bcf8da214fa3e205f19e95f86a03c`

Existing bit-identical files are reused without writes. Absent slots are created exclusively from the pinned packet copies. Any differing file is refused, never overwritten. Control references retain their prior approved UNC child identity. All inputs are opened read-only; derivatives go into the new packet only.

## Separate cache-route supplement

The already pinned `slduiu+0x13aaed7` call and `+0x13aaedc` return occur in the ordinary pre-event7 detailing preparation route. An optional owned DbgEng adapter must arm before SaveAs, pair actual thread/frame/requested ID with the raw null/non-null return, and prove instruction restoration and detach. A successful note lifecycle is independent of that observation. An absent delivered stop is UNOBSERVED; it is not a fallback or cache success. The existing aggregate observer waits for event7 and cannot be reused unchanged for these earlier sites. Its restoration and ownership helpers can be reused with an explicit pre-event7 verifier. This supplement is intentionally outside the frozen six-phase COM packet.
