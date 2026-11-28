# Git toolchain launchers

The Git executable used by checkout might appear to identify the executable selected by a later Python process.
Inside Git Bash, Python can instead select `Git/ucrt64/bin/git.exe` from the inherited path.
Removing only `bin/git.exe` then leaves the toolchain directory instead of the Git distribution root.
The same assumption affects the `mingw64/bin` layout.

Check for the actual Bash executable at both supported distribution-root depths.
Keep executable existence checks and native Windows execution.
See [the native failure](https://github.com/TryUniCAD/Kit/actions/runs/45074594908/job/137369105358).
