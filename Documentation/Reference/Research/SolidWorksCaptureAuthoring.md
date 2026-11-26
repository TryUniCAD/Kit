# Run the SOLIDWORKS capture harness

Use a licensed 64-bit SOLIDWORKS installation with an English part template and Windows PowerShell 5.1. The harness uses the registered SOLIDWORKS COM server. Check the revision it reports before comparing the results to the original SOLIDWORKS 2026 build `34.4.1`.

The [audited authoring source](https://github.com/TryUniCAD/Kit/blob/ea5ae8074eb0ed6d128ac59adc43b438e2ab8d77/re/automation/PairedCaptures/SolidWorksAuthoring/SolidWorksCapture.cs) has SHA-256 `0e90cdfc47f4295e15907505c9870620bb8fab2f82437d57a7f7521c22adb238`. The [historical capture contract](../../Changes/Research/Automation/CaptureHistoryBinding.md) keeps that source fixed and pins the [current capture programme](../../../re/automation/CaptureTools/SolidWorksAuthoring/SolidWorksCapture.cs) separately. The [launcher](../../../re/automation/CaptureTools/SolidWorksAuthoring/RunSolidWorks.ps1) resolves the recipe and control from the repository and requires an explicit destination and case.

1. Close or save open SOLIDWORKS work and use an isolated application session. Choose an unused output location outside the repository's capture folders.
2. Run the first phase for an explicit case. Set the interop path to the installed `SolidWorks.Interop.sldworks.dll` for the registered build.

   ```powershell
   powershell.exe -NoProfile -STA -File re/automation/CaptureTools/SolidWorksAuthoring/RunSolidWorks.ps1 -Recipe P01 -Phase first -OutputDirectory C:/Temp/KitCapture -InteropAssembly 'C:/Path/SOLIDWORKS/SolidWorks.Interop.sldworks.dll'
   ```

3. Quit SOLIDWORKS fully after the first phase finishes. Run the same command with `-Phase second`. The harness requires a different application process ID from the first phase and verifies the unchanged baseline-A SHA-256 before continuing.
4. Inspect the new case directory for both baselines, edited and variant parts, `measurements.json`, and `receipt.json`. Keep the original capture bundles and their digests intact. Repeat runs produce new evidence, including new native file hashes.

For discovery use P01, P03, and P04. Keep P02 reserved for circular-sketch qualification and P05 reserved for frozen-rule holdout evaluation. The launcher selects only the named case.

The original capture record documents the independently authored fixtures and their measured results. The checked-in launcher received a static syntax check after its paths were made configurable. [SOLIDWORKS capture entry](../../Changes/Research/SolidWorksPairedCaptures.md)

## Queued circular readback

Use the existing installation configuration and a dedicated licensed Windows desktop with SOLIDWORKS build `34.4.1.1011`.
The queued `p02-readback` operation reads the five pinned circular controls with healthy controls and a directly owned native process.
Start its listener with the explicit operation.

```powershell
python -B re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py --installation C:/KitPrivate/Installation.json --readback-operation p02-readback listen --interop 'C:/Program Files/SOLIDWORKS Corp/SOLIDWORKS/SolidWorks.Interop.sldworks.dll'
```

Configure the supervisor runner with the same installation path and `--readback-operation p02-readback` before `dispatch`.
Set the controller job options to its exact `source_revision` and `readback_operation` with value `p02-readback`.
Use the [native testing procedure](../../Tasks/Research/AutomationNativeTesting.md) for the controller store, installation, runner and resource configuration.
The successful artifact roster contains `readback.plan`, `readback.measurements`, `readback.receipt` and `dispatch`.
The receipt requires five observed files and five `circle_bindings_verified` results.

Timeout recovery uses the existing listener flags and supervisor rearm protocol.
The archived rearm verifier checks the P02 operation against the retained job definition.
The listener and dispatcher verify their Windows safety helpers against the installation's configured source revision.
Changed helper bytes fail admission before queued native work.

These observations remain unqualified research evidence.
P02 qualification requires independent evidence admission and the frozen-rule protocol.
See [the A08f change](../../Changes/Research/Workers/SolidWorks/CircularReadbackQueue.md) for process verification and the native build prerequisite.
