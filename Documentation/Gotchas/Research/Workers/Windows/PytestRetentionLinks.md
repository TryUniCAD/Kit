# Pytest retention links on Windows

## Expectation

A completed pytest temporary root can be moved to another drive as a tree of ordinary files and directories.

## Observed behavior

Completed Windows runs left directory symbolic links named `pytest-current` and `Check…current` inside the temporary roots. Their targets were absolute paths within their respective original task roots. A transfer guard stopped at those links before changing the source. Following the links could duplicate evidence or traverse outside the intended tree if a target were different. Recreating an absolute link on another drive could leave it pointing back at the old location.

## Workaround

Confirm that the test processes have ended and that the temporary root belongs to the task. Inventory regular files by relative path, byte size and SHA-256, and record each symbolic link's target separately without traversing it. Archive the tree without dereferencing links. Verify the archive against the complete file and link inventory and recheck the original inventory before removing the confirmed task-owned originals. Remove symbolic link nodes without following their targets. Keep the link inventory with the archive and inspect it before extraction because its original absolute targets may no longer exist.

This procedure preserved 735 files and 15 symbolic link targets across five completed roots. The process runs are described in [the Fusion scope attribution verification record](https://github.com/TryUniCAD/Kit/blob/3edbac6ee0d6295162b10ef08d89c0f5e400e7aa/Documentation/Changes/Research/Encoder/FileScopeAttribution.md).
