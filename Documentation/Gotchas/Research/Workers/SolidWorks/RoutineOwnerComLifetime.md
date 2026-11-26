# Keep the routine COM lifetime inside C sharp

The first routine-owner probe returned a typed application interface through PowerShell before invoking its service loop.
The next interface call failed with `TYPE_E_ELEMENTNOTFOUND`.
Cleanup also encountered the transport error.
The precise runtime callable wrapper failure was not isolated.

The owner now attaches, serves requests and releases the interface inside one typed C sharp call.
PowerShell retains only the directly launched native process handle.
Two subsequent P01 batches completed in the same process.
The original failure remains in the private probe directory.
