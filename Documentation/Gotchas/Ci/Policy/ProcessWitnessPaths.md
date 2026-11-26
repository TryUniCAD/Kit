# Process witness paths and security analysis

## Expectation

A test-only child process can appear safe when its parent supplies all input paths.

## Actual behavior

The first streaming witness accepted its target directory and a telemetry output filename through `sys.argv`.
The [source audit](https://github.com/TryUniCAD/Kit/actions/runs/45184196998/job/137725429921) reported two blocking `py/path-injection` findings for those file operations in `BulkScanProcess.py` at source `893e97b95697bf896356ae232531420a432d03a6`.
A trusted caller in the process test did not establish a constrained child-process path contract.

## Workaround

Use a fixed fixture location and return telemetry through a controlled output record.
Keep real directory enumeration and command execution intact.
Do not suppress the security query or relax its blocking gate.
The repaired helper requires a fresh source audit; a passed prior revision does not verify changed process code.
