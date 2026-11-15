# Parallels current-user argument order

## Expectation

The current-user option can precede the virtual machine name.

## Observed behavior

`prlctl exec --current-user "Windows 11"` fails to find the virtual machine.
Without the option, execution uses the system account, which cannot access
the interactive SOLIDWORKS COM server.
The [2026 re-verification](../../../../re/solidworks/v2026/Reverification.md)
records this observation.

## Workaround

Put the option after the virtual machine name:

```sh
prlctl exec "Windows 11" --current-user cmd /c "..."
```

Keep this command in research tooling. Production conversion cannot use the CAD application.
