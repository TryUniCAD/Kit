# Attached Top-plane box source protocol

This source-only protocol reproduces the [disclosed FreeCAD F14c placement](../../../solidworks/records/SdkFreecadOriginBox2026.md#retained-freecad-source-inventory) in the SOLIDWORKS 2026 SP05.2 oracle.
The disclosed profile uses three positive length drivers of 20, 30, and 10 mm.
The authored rectangle spans positive local U and negative local V.
The reversed blind boss follows negative model Y.

The native Top sketch basis must be U = +X, V = −Z, N = +Y at the model origin.
The source dimensions predict the world box independently of the measured transform.
For length L, width W, and height H, the bounds are (0, −H, 0) to (L, 0, W).
The predicted volume is L × W × H and the centroid is (L/2, −H/2, W/2).

The observer checks the signed sketch geometry directly after the rectangle call.
It verifies the real Top-plane parent, four ordinary edges, full constraint, and the origin coincidence.
The external origin point in the relation is a sketch-owned proxy.
The observer checks its native type and ownership alongside the real corner ID.
It preserves the separately selected model origin's ID.
The source keeps the three named driving dimensions and Body name.
The independent solid check compares all eight corners, topology, volume, area, and centre of mass.
[Prior native Top frame](../../../solidworks/records/PrincipalPlaneHandles2026.md) · [Native point ownership](../InspectSdkCornerOwners.py#L117) · [Vendor sketch transform example](https://help.solidworks.com/2026/english/api/sldworksapi/Transform_Coordinates_from_Sketch_to_Model_Space_Example_VB.htm) · [Vendor extrusion direction contract](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.ifeaturemanager~featureextrusion3.html)

## Freeze the packet

Use a committed Kit checkout. Use a pristine rectangle control whose SHA-256 is `c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57`.
Choose an unused Mac packet directory visible from Windows through Parallels.
Choose an unused Windows-local `C:\KitAttachedTopBoxSourcesNN` directory for the private evidence.

```sh
PYTHONPATH="$KIT/re/tooling/sw2026" uv run --no-project --python 3.13 python -B \
  "$KIT/re/tooling/sw2026/attached_top_box_source/RunAttachedTopBoxSources.py" \
  prepare "$CONTROL" "$PACKET" \
  --guest-private-root 'C:\KitAttachedTopBoxSources01' \
  --cohort disclosed --revision "$COMMITTED_SHA"
```

The preparer checks each copied tool against the committed revision.
It reports the SHA-256 of `Job.json`.
Use that exact digest for guest execution.

## Run the source batch

Only the oracle owner uses the Windows 11 VM.
Use the existing guest Python with the registered pywin32 support.
Invoke it through `prlctl exec "Windows 11" --current-user` and an encoded PowerShell command.
Pass absolute guest-visible paths to the original packet.

```powershell
& $GuestPython -B "$GuestPacket\Tools\RunAttachedTopBoxSources.py" run "$GuestPacket\Job.json" --job-sha256 $JobSha
```

The disclosed batch requires four distinct SOLIDWORKS processes. They measure the pristine control, author the source and three separately edited saves, reopen them, then measure the final control.
Every edit changes one driver. The author rebuilds after restoring its original value before the next edit.
The fresh reader opens every saved sibling read-only with zero errors and warnings.
All source artifacts stay immutable during reopen.

For held-out source locks, prepare a separate packet with `--cohort sealed` and a fresh guest-private root.
The guest chooses two independent positive size triples and three edits per triple.
The sealed batch requires six distinct fresh SOLIDWORKS processes and both healthy controls.
The public `Result.json` contains the spec digest, artifact identities, phase record hashes and process identities.
The guest-local directory retains the source bytes, solver observations, exact dimensions and COM logs.
Keep those sealed inputs private during writer derivation.
A failed phase records its status and preserves the private diagnostic.
[Parallels transport](../../../../Documentation/Gotchas/Conversion/Solidworks/Tracing/ParallelsPowerShellNeedsEncodedCommands.md)

## Completion boundary

This prepares a source fixture and an independent observer.
The healthy-control result comes from the actual native run.
The protocol generates zero Kit-written files and grants zero FCStd conversion credits.
