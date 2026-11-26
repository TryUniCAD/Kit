# Windows locks an active tool executable during reinstallation

An installed CLI can remain open while its child catalogue worker runs.
Windows then locks the launcher and interpreter executables.
A forced `uv tool install --reinstall` can remove package files before failing to replace those executables.
The tool can temporarily lose imports even though its original run remains alive.

Wait for the tool's normal exit before reinstalling its environment.
Do not terminate another operation to release the lock.
The desktop incident was recovered by restoring the same package versions into the existing environment without replacing its locked executables.
The installed command, NumPy, Windows API imports, and original process identity were verified afterward.
This recovery does not establish acceptance of the running catalogue's native cases.
