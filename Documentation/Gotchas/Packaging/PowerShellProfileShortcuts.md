# PowerShell profile shortcuts do not configure the installed executable

A profile function can supply defaults for `kit run solidworks`.
It applies only when that profile has loaded in the current shell.
An existing terminal, `-NoProfile`, or a profile authorization failure can still invoke the unconfigured `kit.exe`.
The executable then correctly requires `--root`.

The desktop failure reproduced that argument error after the executable was installed globally.
Use [saved CLI defaults](../../Changes/Commands/SavedRunDefaults.md) for profile-independent startup.
Verify the executable from Windows PowerShell with `-NoProfile`.
Do not infer that a function in a different shell configured the user's terminal.
