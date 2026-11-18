# Preserve companion files during path publication

Registry path writes with `overwrite=False` publish files with an exclusive
filesystem operation. A file created after the destination scan raises
`FileExistsError` and stays intact. The registry rolls back files published
earlier in that write. When replacement is enabled, the registry records
each completed backup before moving the next target so rollback can recover
from a partial backup failure.

The registry integration suite exercises both failures through the
ordinary staged write path and verifies the final directory contents.
Multi-file output still uses separate filesystem operations.

[Path destination behavior](../../Reference/Architecture/Engine.md#path-destinations)
