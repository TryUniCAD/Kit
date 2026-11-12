# A drawing open can wait forever for the drawing engine

Fusion 2706.1.17 opens a drawing through a separate drawing engine process, `AcCoreConsole`.
Fusion first writes the embedded DWG and a SAB export of the referenced body to a temporary folder.
It then starts the engine and waits for an IPC connection.

The `P3SwappedDwg` variant stopped in that wait.
It combines the A1 segments with the A0 DWG.

| Observation                          | Value                                                  |
| ------------------------------------ | ------------------------------------------------------ |
| Fusion main thread                   | `AcCoreServer::startCoreView` in `IpcManagerImp::wait` |
| Engine main thread                   | Idle in its message loop                               |
| Engine session header in its log    | Not written                                            |
| Duration before intervention         | 3 minutes 27 seconds                                   |
| After the engine process was stopped | Fusion stayed in the same wait                         |

`Documents.open` did not return, so the script could not record an error.
Only stopping Fusion released the oracle.

The cause is not known.
A mismatch between the segments and the DWG does not explain it by itself.
`P5ReverseSwap` pairs the A0 segments with the A1 DWG, and it opened normally.
`P4ViewsControl` also opened the same A0 DWG with its own segments.

The engine start time varies between opens.

| Open                       | Engine start to session header |
| -------------------------- | ------------------------------ |
| `M1Reemitted`, first open  | About 45 seconds               |
| `P4ViewsControl`           | 99 seconds                     |
| `P3SwappedDwg`             | No header after 207 seconds    |

Open untrusted drawing variants last in an unattended run.
Write a checkpoint before each open, so that a stall identifies the variant.

A forced stop of Fusion can leave its helper processes alive.
Its bundled `node` helper and the crash reporter kept the script bridge port open.
The relaunched Fusion then had no bridge until those helpers stopped and Fusion started again.
