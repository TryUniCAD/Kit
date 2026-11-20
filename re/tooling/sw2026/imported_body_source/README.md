# Native imported body source protocol

This protocol authors and measures one solid with an imported base feature in
SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`. It belongs to the native import
research in [PR #121](https://github.com/TryUniCAD/Kit/pull/121).

The disclosed input creates a temporary box on the configured native part
template. Its lower face centre is (7, −11, 4) mm. The box measures 19 mm
along X, 27 mm along Y and 13 mm along +Z. Those inputs predict bounds from
(−2.5, −24.5, 4) mm to (16.5, 2.5, 17) mm, volume 6669 mm³, area 2222 mm²
and centre of mass (7, −11, 10.5) mm.

The author passes a nine-double array to `IModeler::CreateBodyFromBox3`. It holds
the face centre and lengths in metres and the +Z unit vector. The author passes the resulting temporary
solid to `IPartDoc::CreateFeatureFromBody3` with reference-surface creation
disabled and the body check bit enabled. The body check runs without the
simplification option. The first exact-build source attempt observed a
feature named `Imported1` reporting type `BaseBody` after rebuild.
The observer requires `BaseBody` from `GetTypeName2`.
[2026 temporary box](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModeler~CreateBodyFromBox3.html) · [2026 native import call](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IPartDoc~CreateFeatureFromBody3.html) · [2026 body creation flags](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swCreateFeatureBodyOpts_e.html) · [2026 feature types](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeature~GetTypeName2.html)

The observer checks the eight expected corners, the twelve line edges and the
six planar face loops with their edge incidence. It measures one solid, volume,
area and centre of mass against the analytic box in SI units. Every face of the
solid must resolve to the actual import as its oldest feature owner. The native
object identity checks tie the feature's faces to the same public solid. The
saved feature reference must resolve in a fresh process before rebuild. Each
phase records the complete feature tree, feature errors, and the exact file and
process identities. [2026 feature face ownership](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeature~GetFaces.html) · [2026 face body](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFace2~GetBody.html) · [2026 persistent reference resolution](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDocExtension~GetObjectByPersistReference3.html)

## Prepare both cohorts before deriving a writer

Use a committed Kit checkout and the pristine rectangle control with SHA-256
`c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57`.
Use an unused Mac packet directory outside the checkout, visible from Windows
through Parallels. Choose a new Windows-local
`C:\KitImportedBodySourcesNN` folder for the private evidence.

```sh
PYTHONPATH="$KIT/re/tooling/sw2026" python3 -B \
  "$KIT/re/tooling/sw2026/imported_body_source/RunImportedBodySources.py" \
  prepare "$CONTROL" "$PACKET" --guest-private-root 'C:\KitImportedBodySources01' \
  --cohort disclosed --revision "$COMMITTED_SHA"
```

The preparation step checks each copied tool against the specified commit. It
reports the `Job.json` SHA-256. Prepare another packet with `--cohort sealed`
and a separate unused Windows root. The two held-out boxes are sampled inside
the guest with independent dimensions and translated lower face centres. Run
the sealed source batch before starting writer derivation and preserve the
resulting hashes and time of the lock.

## Run the source batch

The oracle owner uses the existing Windows 11 guest Python with pywin32.
Invoke it through `prlctl exec "Windows 11" --current-user` and an encoded
PowerShell command. Use absolute guest paths and the preparer's exact job digest.

```powershell
& $GuestPython -B "$GuestPacket\Tools\RunImportedBodySources.py" run "$GuestPacket\Job.json" --job-sha256 $JobSha
```

The disclosed batch uses four distinct SOLIDWORKS processes. The sealed batch
uses six. A guest-local copy of the fixed pristine control brackets each batch, using the same
[control function](../AuthorRectangleAnchors.py#L279) and
[versioned COM session](../Swapp.py#L214) as existing source probes.
Each sample has one process for native authoring, rebuild and save and
another for a clean read-only reopen and a further rebuild. The saved source
remains immutable. A failed phase or bracket leaves the batch unqualified.

For each sealed slot, the shared `Result.json` contains source, specification
and phase record SHA-256 digests plus opaque slot labels and phase status.
Keep the native source bytes, geometry, persistent references, COM logs and
specified values in the Windows-local directory. The disclosed receipt
additionally exposes its modeler inputs and cold geometry observations.
[Parallels command transport](../../../../Documentation/Gotchas/Conversion/Solidworks/Tracing/ParallelsPowerShellNeedsEncodedCommands.md)

## Use the results

The [source receipt](../../../solidworks/measurements/2026/ImportedBaseBodySourcesNative01.json)
binds four disclosed and six sealed phases with healthy controls. The
[archive record](../../../solidworks/records/ImportedBaseBody2026.md)
identifies the serialized `moBaseBody_c` schema 1 wrapper and its shared
import serializer. Invoke `python3 -B ReplayImportedBaseBody.py DISCLOSED_SOURCE`
with the exact disclosed hash to measure five byte-exact linked streams
through the schema 1 archive trunk. The script reports hashes and measured
field order. The two sealed sources stay private.

The [envelope probe](LocalBodyEnvelope.py) accepts the same disclosed source
and re-emits the ordinary local-body record and the body-free configuration
partition. The JSON records the separate stream hashes, resolved atom and
selected mark. See the [storage record](../../../solidworks/records/ImportedBaseBody2026.md#separate-local-body-storage).

Use `--cohort contrast` and a new guest-local root to author a translated
box and two matched feature and body name variants. The variant source
producer uses the same controls, hash checks and persistent geometry
observer. A passing batch shares only those three disclosed source files
and their checked public observations. The sealed cohort remains private.
[Feature name API](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeature_members.html)
· [Body name API](https://help.solidworks.com/2024/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IBody2~Name.html)

Use [InspectImportedBodyContrast.py](InspectImportedBodyContrast.py) with
the completed packet and `--native-receipt-sha256`. It checks all three
disclosed source identities, the field and attribute owners, and exact
re-emission of the seven measured streams for each case.

Use `--cohort topology` with a fresh guest directory to author the
disclosed +Z and −Y cylindrical solids. The modeler gives each body
two planar caps and one analytic cylinder. The observer checks the
actual axis, radius, solid and exact face owner before saving and
after a separate fresh reopen. The two source variants let the archive
inspection compare object counts across different geometries.
[Temporary cylinder API](https://help.solidworks.com/2024/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModeler~CreateBodyFromCyl.html)

## Lock private cylindrical sources

Prepare a separate packet with `--cohort sealed-topology` and a new
`C:\KitImportedBodySourcesNN` guest directory. The host packet contains the
frozen author tools, job and pristine rectangle control. The preparer prints
the exact job digest. Verify the frozen packet without opening SOLIDWORKS.

```sh
python3 -B "$PACKET/Tools/RunImportedBodySources.py" run "$PACKET/Job.json" \
  --job-sha256 "$JOB_SHA" --verify-only
```

The oracle owner then runs the same command with guest paths and omits
`--verify-only`. The author draws two independent translated cylinders with
different signed oblique axes inside Windows. It writes and hashes the
private specifications before the first control process. Both parts come
from SOLIDWORKS creating and attaching a temporary solid.

Each author process observes the solid before and after saving. A fresh
process reopens each saved source read-only and compares the cold and rebuilt
states. The observer checks the sole BaseBody feature and persistent face
ownership, the outward caps, both full circular rims, six directional bounds,
volume, area and centre of mass. Both pristine controls and all four source
processes must pass. The source and specification hashes must still match
after the final control.

Retain the aggregate `Result.json` from the packet. A passing result records
two opaque source hashes, two specification and source lock times, six
distinct processes, eight periodic observations and zero shared held-out
payloads. The native parts, salted specifications, persistent references and
per-phase measurements stay inside the guest. Freeze this source receipt
before implementing the typed neutral-source writer. Candidate generation
and acceptance need their own later evidence.

## Observe a standalone body in the native kernel

Run [ObserveKernelBodyRestore.py](ObserveKernelBodyRestore.py) from a
committed tool packet with the same source observer and versioned COM
helpers. The job selects a new `C:\KitKernelRestoreNN` directory and binds
all tool digests, raw file digests and expected SI geometry. Each case
declares whether it is a vendor-authored local body control or a generated
disclosed body. Invoke the tool through the same Parallels current-user
transport with the job checksum.

The probe first calibrates the automation route with a temporary body
saved to a native IStream and returned through `IModeler::Restore`. The
candidate lanes use the same restore and attachment calls. Each phase
checks its process image, exact topology, vertices, volume, area and centre
of mass. The last two phases repeat the raw and pristine application
controls. Candidate acceptance requires successful bracketing controls.
[Native restore interface](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModeler~IRestore2.html)
· [Temporary solid measurement](https://help.solidworks.com/2024/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IBody2~GetMassProperties.html)

The dynamic and typed out-of-process restore controls return the same
interface error on the native stream. Use
[ObserveKernelExchange.py](ObserveKernelExchange.py) with the packet's
exchange binding and that additional tool digest to compare binary
Parasolid exchange in a fresh guest directory. Both ordinary controls
export the native box as `.x_b` before the import. The original
3D Interconnect setting is recorded and restored in each phase.
[Binary Parasolid translator](https://help.solidworks.com/2026/english/SolidWorks/sldworks/c_parasolid_files.htm)

The packet authors source fixtures through SOLIDWORKS. It records zero Kit
writer outputs and zero native writer acceptance. The public conversion route
and any opt-in capability-loss behavior require separate implementation and
acceptance evidence.
