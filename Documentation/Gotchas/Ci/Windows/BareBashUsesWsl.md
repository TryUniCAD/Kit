# Bare Bash resolves to WSL

A native Windows Python process might resolve `bash` to the Windows Subsystem for Linux launcher.
The hosted runner has no installed Linux distribution, so the reporting subprocess exits before running the script.
The surrounding workflow can still use Git Bash successfully because its shell is selected separately.

Resolve the Git Bash executable beside the installed Git distribution for native Windows reporting fixtures.
Keep execution native; do not install WSL or bypass the report verifier.
See [the failed native process](https://github.com/TryUniCAD/Kit/actions/runs/45073400945/job/137365426250).
