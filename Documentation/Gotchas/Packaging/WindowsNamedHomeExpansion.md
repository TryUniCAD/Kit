# Named home expansion differs on Windows

An unknown `~user` path does not always raise an expansion error on Windows.
Python can construct a sibling user-directory path from the current profile.
The missing account is then discovered only when a later operation reads or creates that path.
The desktop process checks observed downstream missing-file and access errors instead of the expected loader error.

Saved run paths now accept only the current user's home syntax.
Named-user home paths are rejected before research starts, with the normal JSON validation error.
Use an explicit absolute path for another directory.
See [saved run defaults](../../Changes/Commands/SavedRunDefaults.md).
