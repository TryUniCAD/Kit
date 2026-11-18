# Companion file creation can race the destination scan

A second process can create a companion after the registry scans for
existing output paths. An unconditional replace at publication then
overwrites the other process's new file despite `overwrite=False`.

Use an exclusive filesystem operation to publish each file. Keep the
identity of each published output so rollback removes only files that
still belong to the current write. The bundle regression creates a
companion inside the publication window and verifies both its contents
and the rollback of the primary output.

[Registry integration proof](../../../../tests/Convert/Registry/RegistryRaceTests.py)
