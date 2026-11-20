# Companion file creation can race the destination scan

A second process can create a companion after the registry scans for
existing output paths. An unconditional replace at publication then
overwrites the other process's new file despite `overwrite=False`.

Use an exclusive filesystem operation to publish each file. Record the
identity of each published output and check it before rollback. The bundle
integration case creates a companion during publication and checks its
contents and the rollback of the primary output.

[Registry integration case](../../../../tests/Convert/Registry/RegistryRaceTests.py)
