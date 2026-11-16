# Inventory output and transport status are separate evidence

## Expectation

A process inventory that prints the expected JSON also establishes successful command execution and guest cleanup.

## Actual behavior

After the corrected radial reopen/edit batch, a read-only PowerShell inventory printed the three expected license processes but returned exit `1`. A subsequent invocation returned Parallels `255` with `PrlJob_GetRetCode: Invalid argument` and no process data. Neither outcome establishes a successful postflight. The evidence does not identify a license failure or authorize service or VM changes.

The host supervisor likewise reports guest state as unknown after a clean transport exit. Its successful return does not prove the CAD process exited.

## Workaround

Keep each command's exit status, stdout, stderr and observation time. Preserve unsuccessful receipts rather than replacing them. An independent direct invocation of `C:\Windows\System32\tasklist.exe /FO CSV /NH` through `prlctl exec "Windows 11" --current-user` succeeded with exit zero and a complete CSV result. Filter that recorded data for the CAD and license process names, retain its raw-output hash, and report the observed process state separately from native measurement success.

This read-only fallback observed no SOLIDWORKS process and unchanged license-process IDs. It started no CAD/COM session and changed no service, license or VM state. The [fresh training receipt](../../../../../re/solidworks/measurements/2026/RadialTrainingReopenEdit02.json) records the successful inventory independently of transport cleanup.
