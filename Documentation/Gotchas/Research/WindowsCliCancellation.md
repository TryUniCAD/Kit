# Windows CLI cancellation needs console process groups

## Expectation

The installed research CLI should launch the Windows supervisor and allow it to settle workers when cancelled.

## Actual behavior

At `9e2049c7`, the CLI rejected Windows supervisor commands despite the underlying supervisor's native Windows implementation.
The launcher did not own Windows cancellation handlers, and its forwarding function imported POSIX-only signal names.
A blocking Windows process wait also delayed Python signal dispatch until the child exited.

## Workaround

Use the updated CLI with Windows 10 or newer, Python 3.14 or newer, and the locked `pywin32` development extra.
The launcher starts a separate process group and forwards handled cancellation as `CTRL_BREAK_EVENT`.
The supervisor handles `SIGBREAK` through its existing shutdown path.
The selected checkout must advertise Windows CLI shutdown protocol 1; older checkouts are rejected before launching workers.
Bounded waits allow the launcher to dispatch pending cancellation while its child remains active.

The launcher and supervisor must share a Windows console.
A forced process termination cannot run Python signal handlers or forward cancellation.
Use the supervisor's existing lease and recovery controls after forced termination.

See the [Python subprocess control-event contract](https://docs.python.org/3.14/library/subprocess.html#subprocess.Popen.send_signal)
and the [Windows launcher change](../../Changes/Research/Supervisor/Cli/WindowsLauncher.md).
