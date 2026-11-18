# An invalid Parallels job can precede native progress

The first transport attempt at the H01 source reopen returned 255 with `PrlJob_GetResult: Invalid argument`. It produced no guest phase record. An independent task inventory found the license server healthy and no owning SOLIDWORKS or Python process. Retrying the same reopen generated the expected phase record, then the edited reopen and trailing control passed.

Keep both transport reports, check Windows process inventory and terminal guest records, and use the bracketed native results for acceptance. [Packet05 source receipt](../../../../../../re/solidworks/measurements/2026/PerpendicularMateSourcePosition05.json)
