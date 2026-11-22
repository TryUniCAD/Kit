# Disclosed ellipse seam snapshot discriminator

The snapshot packet isolates the missing position transition from the [exact allocator trace](EllipseSeamAllocation2026.md). It reuses only disclosed Front A geometry from the successful [original source lock](../measurements/2026/EllipseBlindBossDisclosedLock01.json). The centre is (18.25, −6.375) mm, the semiaxes are 21.375 and 8.875 mm, the signed major angle is 28.75 degrees and the positive boss D1 is 13.125 mm. The same code, inputs, 34.5.2.0604 x64 application and exact blank part template drive the two independent branches. Both use the registered AddToDB direct path. A distinct sketch-only and blind-boss save separates stage effects without changing either original disclosed asset.

## Native procedure

1. Fresh-open and rebuild the exact disclosed rectangle and circle controls. Verify the installed 34.0 API declarations. The source observer uses the documented dispatch start and end methods on an explicitly typed `ISketchEllipse`. It surveys the two sketch point inventories when registered. Both channels record scoped point type, owning sketch, complete ID pair and XYZ. Null and unregistered channels are retained as limits. A returned foreign sketch point stops the phase. [Ellipse interface](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISketchEllipse.html) · [Start point API family](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISketchEllipse~IGetStartPoint2.html) · [End point API family](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISketchEllipse~IGetEndPoint2.html) · [Scoped sketch point ID](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISketchPoint~IGetID.html)
2. In the first fresh process, author the one full ellipse in a canonical Front sketch. Sample while the sketch is active immediately after drawing, after closing it, after its clean document rebuild before saving and immediately after saving. Verify one actual closed contour, one profile, unchanged signed geometry, zero relations, one active configuration, and zero solid and sheet bodies. Save `EllipseSketchOnly.SLDPRT` with zero errors and warnings.
3. In the second author process, independently draw the same ellipse and take the same snapshots. Also observe immediately after creating the ordinary blind boss and before the explicit rebuild. Require the exact editable D1 owner, one owned solid with two caps, complete elliptical trims, six-significant-figure area, volume and centre of mass, and the original bounds/feature checks. Save `EllipseBlindBoss.SLDPRT` with zero errors and warnings.
4. Each exact save is reopened read-only in its own fresh process immediately after its author phase. Sample cold and after the checked rebuild. Require immutable bytes, correct document identity, healthy role-specific body count and the full native tree. Run the rectangle and circle controls again. The batch requires eight distinct processes and a final idle oracle. The batch continues to the final controls when a source phase fails.

The terminal result binds the job SHA-256, application build, phase-result and artifact digests. On the host the separate guarded analyzer binds the saved Config-0 and ResolvedFeatures maps, actual profile/datum, inline ellipse, seam endpoint ordinal and mapped handle. The analyzer compares live and stored centre/axis coordinates and their actual point creation words. A live endpoint binding requires the true owner, a separate axis-independent ID and the matching seam creation word. Paired direct getters must agree when both return a point. Inventories give an independent view of visible IDs and candidate rows. A movement is reported only across two observations in the same process with the same scoped point ID and independently unchanged ellipse. Distinct archive positions or omitted public endpoints are separately recorded. A sketch-only archive outside the proven typed reader retains its precise refusal.

## Staging and analysis

Freeze from the exact committed packet revision, on the host. The packet uses the prior disclosed lock, one semantic input, an independent analytic prediction and two existing controls. It contains no protected assets.

```sh
python3.14 -E -B re/tooling/sw2026/ellipse_source/EllipseSeamPacket.py \
  --revision <full-packet-commit> \
  --output /Users/odin/Documents/UniCAD/Oracle121Takeover/EllipseSeamDiscriminator01/Packet \
  --guest-root 'C:\KitEllipseSeamDiscriminator01'
```

After the host prints the job digest, the designated oracle owner stages the share copy and runs the guest-local job with that digest. Capture files remain under the named guest root. Preserve the full terminal result and copy only the disclosed output files and records needed for the host analyzer.

```sh
seam_python='C:\Users\odin\AppData\Local\Programs\Python\Python312\python.exe'
seam_share='\\Mac\Home\Documents\UniCAD\Oracle121Takeover\EllipseSeamDiscriminator01\Packet'
seam_guest='C:\KitEllipseSeamDiscriminator01\Packet'
prlctl exec 'Windows 11' --current-user "$seam_python" -E -B "$seam_share\Tool\RunEllipseSeam.py" \
  --job "$seam_share\SeamJob.json" --pin <job-sha256> --stage
prlctl exec 'Windows 11' --current-user "$seam_python" -E -B "$seam_guest\Tool\RunEllipseSeam.py" \
  --job "$seam_guest\SeamJob.json" --pin <job-sha256>
```

The terminal path is `C:\KitEllipseSeamDiscriminator01\Capture\SeamResult.json`. On the exact frozen analysis checkout, compare the independently copied disclosed capture with both original digests.

```sh
python3.14 -I -B re/tooling/sw2026/ellipse_source/AuditEllipseSeam.py \
  --job /absolute/path/to/Packet/SeamJob.json --pin <job-sha256> \
  --capture /absolute/path/to/disclosed/Capture --result-pin <native-result-sha256>
```

The packet measures when the seam moves or first becomes observable. A native position change supplies temporal ownership evidence. Source constructor semantics still need the proven producer or an independently measured alternate state. [CAD acceptance criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Generative corpus](../../Playbook/GenerativeCorpus.md)
