# A process can exit during a proc stat read

On Linux a process can disappear between a successful signal-zero probe and reading its stat entry. If the entry has already opened, the read can raise ProcessLookupError. Opening the missing entry can instead raise FileNotFoundError.

The supervisor cleanup test treats either result as evidence of exit when procfs is available. A live child still has to disappear before the timeout. [Hosted process cleanup failure](https://github.com/TryUniCAD/Kit/actions/runs/44761866584/job/136376854582)
